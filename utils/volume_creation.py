"""
Utilitaires pour la création de volumes VeraCrypt.
"""

import os
import logging
import subprocess
from typing import List, Tuple, Dict, Optional
from .sudo_session import sudo_session
import time
import random
import string

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.veracrypt/veracrypt.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('veracrypt.volume_creation')

class VolumeCreation:
    # Algorithmes de chiffrement disponibles
    ENCRYPTION_ALGORITHMS = {
        'AES': 'aes',
        'Serpent': 'serpent',
        'Twofish': 'twofish',
        'Camellia': 'camellia',
        'AES(Twofish)': 'aes-twofish',
        'AES(Twofish(Serpent))': 'aes-twofish-serpent',
        'Serpent(AES)': 'serpent-aes',
        'Serpent(Twofish(AES))': 'serpent-twofish-aes',
        'Twofish(Serpent)': 'twofish-serpent'
    }
    
    # Algorithmes de hachage disponibles
    HASH_ALGORITHMS = {
        'SHA-512': 'sha512',
        'SHA-256': 'sha256',
        'Whirlpool': 'whirlpool',
        'RIPEMD-160': 'ripemd160'
    }
    
    # Systèmes de fichiers disponibles
    FILESYSTEMS = {
        'FAT': 'FAT',
        'exFAT': 'exFAT',
        'NTFS': 'NTFS',
        'EXT4': 'EXT4',
        'BTRFS': 'BTRFS'
    }
    
    @staticmethod
    def format_size(size: float, unit: str) -> str:
        """Formate une taille avec son unité.
        
        Args:
            size: Taille en nombre
            unit: Unité (MB, GB, TB)
            
        Returns:
            Taille formatée (ex: '100M', '1G')
        """
        if unit == 'MB':
            return f"{int(size)}M"
        elif unit == 'GB':
            return f"{int(size)}G"
        elif unit == 'TB':
            return f"{int(size)}T"
        return f"{int(size)}M"  # Par défaut en MB
        
    @staticmethod
    def create_volume(
        path: str,
        password: str,
        size: str,
        encryption: str = 'AES',
        hash_algo: str = 'SHA-512',
        filesystem: str = 'FAT',
        hidden: bool = False,
        hidden_size: Optional[str] = None,
        hidden_password: Optional[str] = None,
        pim: Optional[int] = None,
        hidden_pim: Optional[int] = None,
        random_data: Optional[str] = None,
        keyfiles: Optional[List[str]] = None,
        progress_callback = None
    ) -> Tuple[bool, str]:
        """Crée un nouveau volume VeraCrypt."""
        try:
            # Validation des paramètres
            logger.debug("Validation des paramètres d'entrée...")
            
            # Vérifier le chemin
            if not os.path.dirname(os.path.abspath(path)):
                logger.error(f"Le répertoire parent n'existe pas : {os.path.dirname(path)}")
                return False, "Le répertoire parent du volume n'existe pas"
                
            # Vérifier les permissions
            parent_dir = os.path.dirname(os.path.abspath(path))
            if not os.access(parent_dir, os.W_OK):
                logger.error(f"Permissions insuffisantes sur le répertoire : {parent_dir}")
                return False, "Permissions insuffisantes sur le répertoire parent"
                
            # Vérifier l'algorithme de chiffrement
            if encryption not in VolumeCreation.ENCRYPTION_ALGORITHMS:
                logger.error(f"Algorithme de chiffrement invalide : {encryption}")
                return False, f"Algorithme de chiffrement invalide. Valeurs possibles : {', '.join(VolumeCreation.ENCRYPTION_ALGORITHMS.keys())}"
                
            # Vérifier l'algorithme de hachage
            if hash_algo not in VolumeCreation.HASH_ALGORITHMS:
                logger.error(f"Algorithme de hachage invalide : {hash_algo}")
                return False, f"Algorithme de hachage invalide. Valeurs possibles : {', '.join(VolumeCreation.HASH_ALGORITHMS.keys())}"
                
            # Vérifier le système de fichiers
            if filesystem not in VolumeCreation.FILESYSTEMS:
                logger.error(f"Système de fichiers invalide : {filesystem}")
                return False, f"Système de fichiers invalide. Valeurs possibles : {', '.join(VolumeCreation.FILESYSTEMS.keys())}"
                
            # Vérifier l'espace disque disponible
            try:
                size_bytes = VolumeCreation._parse_size(size)
                statvfs = os.statvfs(parent_dir)
                free_space = statvfs.f_frsize * statvfs.f_bavail
                if size_bytes > free_space:
                    logger.error(f"Espace disque insuffisant. Requis : {size_bytes}, Disponible : {free_space}")
                    return False, "Espace disque insuffisant"
            except ValueError as e:
                logger.error(f"Format de taille invalide : {size}")
                return False, f"Format de taille invalide : {str(e)}"

            # Log des paramètres (sans les mots de passe)
            logger.info("Création d'un volume VeraCrypt :")
            logger.info(f"- Chemin : {path}")
            logger.info(f"- Taille : {size}")
            logger.info(f"- Chiffrement : {encryption}")
            logger.info(f"- Hash : {hash_algo}")
            logger.info(f"- Système de fichiers : {filesystem}")
            logger.info(f"- Volume caché : {hidden}")
            if hidden:
                logger.info(f"- Taille du volume caché : {hidden_size}")
            
            # Construire la commande de base
            command = [
                'veracrypt',
                '--text',  # Mode texte
                '--create', path,  # Chemin du volume
                '--encryption', VolumeCreation.ENCRYPTION_ALGORITHMS[encryption],  # Algorithme de chiffrement
                '--hash', VolumeCreation.HASH_ALGORITHMS[hash_algo],  # Algorithme de hachage
                '--filesystem', VolumeCreation.FILESYSTEMS[filesystem],  # Système de fichiers
                '--size', size,  # Taille du volume
                '--volume-type=normal'  # Type de volume normal
            ]
            
            if pim is not None:
                command.extend(['--pim', str(pim)])
            
            if hidden:
                command.extend(['--hidden'])
                if hidden_pim is not None:
                    command.extend(['--hidden-pim', str(hidden_pim)])
            
            # Log de la commande
            log_cmd = command.copy()
            logger.debug(f"Commande préparée : {' '.join(log_cmd)}")
            
            # Préparer les réponses aux prompts dans l'ordre exact
            responses = []
            
            # 1. Mot de passe
            if not password:
                logger.error("Le mot de passe est vide")
                return False, "Le mot de passe ne peut pas être vide"
                
            logger.debug(f"Longueur du mot de passe : {len(password)}")
            responses.append(password)  # Une seule fois dans la liste
            
            # 2. PIM (vide si non spécifié)
            pim_value = str(pim) if pim is not None else ''
            responses.append(pim_value)
            logger.debug(f"PIM : {'(spécifié)' if pim else '(vide)'}")
            
            # 3. Keyfile (vide si non spécifié)
            keyfile = keyfiles[0] if keyfiles else ''
            responses.append(keyfile)
            logger.debug(f"Keyfile : {'(spécifié)' if keyfile else '(vide)'}")
            
            # 4. Données aléatoires
            if random_data:
                responses.append(random_data)
                logger.debug("Utilisation des données aléatoires fournies")
            else:
                random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=320))
                responses.append(random_chars)
                logger.debug("Génération de 320 caractères aléatoires")
            
            logger.debug(f"Nombre de réponses préparées : {len(responses)}")
            
            # Exécuter la commande avec sudo
            logger.debug("Démarrage du processus VeraCrypt...")
            try:
                process = subprocess.Popen(
                    ['sudo', '-S'] + command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1  # Line buffered
                )
                
                # Récupérer et envoyer le mot de passe sudo
                logger.debug("Récupération du mot de passe sudo...")
                sudo_password = sudo_session.get_sudo_password()
                if not sudo_password:
                    logger.error("Mot de passe sudo non disponible")
                    return False, "Mot de passe sudo non disponible"
                
                logger.debug("Envoi du mot de passe sudo...")
                process.stdin.write(f"{sudo_password}\n")
                process.stdin.flush()
                time.sleep(0.2)  # Attendre que sudo soit prêt
                
                # Lire et traiter les prompts de VeraCrypt
                logger.debug("Traitement des prompts VeraCrypt...")
                current_response_index = 0
                
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                        
                    line = line.strip()
                    logger.debug(f"Sortie VeraCrypt : {line}")
                    
                    # Appeler le callback de progression si fourni
                    if progress_callback and "Done:" in line:
                        progress_callback(line)
                    
                    # Gérer les différents prompts
                    if "Enter password:" in line or "Re-enter password:" in line:
                        # Pour le mot de passe et sa confirmation, toujours envoyer password
                        logger.debug(f"Prompt détecté : {line}")
                        logger.debug(f"Envoi du mot de passe : '{password}'")
                        process.stdin.write(f"{password}\n")
                        process.stdin.flush()
                    elif "Enter PIM:" in line:
                        # Pour les autres prompts, utiliser les réponses préparées
                        if current_response_index < len(responses):
                            response = responses[current_response_index]
                            logger.debug(f"Prompt détecté : {line}")
                            logger.debug(f"Envoi de la réponse {current_response_index + 1}/{len(responses)} : '{response}'")
                            process.stdin.write(f"{response}\n")
                            process.stdin.flush()
                            current_response_index += 1
                    elif "Enter keyfile path" in line:
                        if current_response_index < len(responses):
                            response = responses[current_response_index]
                            logger.debug(f"Prompt détecté : {line}")
                            logger.debug(f"Envoi du chemin du keyfile : '{response}'")
                            process.stdin.write(f"{response}\n")
                            process.stdin.flush()
                            current_response_index += 1
                    elif "randomly chosen characters" in line:
                        if current_response_index < len(responses):
                            response = responses[current_response_index]
                            logger.debug(f"Prompt détecté : {line}")
                            logger.debug(f"Envoi de {len(response)} caractères aléatoires : '{response}'")
                            process.stdin.write(f"{response}\n")
                            process.stdin.flush()
                            current_response_index += 1
                    elif "Passwords do not match" in line:
                        logger.error("Les mots de passe ne correspondent pas !")
                    
                    time.sleep(0.2)  # Attendre entre chaque réponse
                
                # Attendre la fin du processus
                logger.debug("Attente de la fin du processus...")
                stdout, stderr = process.communicate(timeout=300)
                return_code = process.returncode
                
                if return_code != 0:
                    logger.error("Erreur lors de la création du volume :")
                    logger.error(f"Code de retour : {return_code}")
                    logger.error(f"Sortie standard : {stdout}")
                    logger.error(f"Erreur standard : {stderr}")
                    
                    # Analyser l'erreur
                    if "too long" in stderr.lower():
                        return False, "Le mot de passe est trop long"
                    elif "do not match" in stdout.lower():
                        return False, "Les mots de passe ne correspondent pas"
                    else:
                        return False, "Erreur lors de la création du volume"
                    
                logger.info("Volume créé avec succès")
                return True, "Volume créé avec succès"
                
            except subprocess.TimeoutExpired:
                logger.error("Timeout lors de la création du volume")
                if 'process' in locals():
                    process.kill()
                return False, "La création du volume a pris trop de temps"
                
            except Exception as e:
                logger.error(f"Exception lors de la création du volume : {str(e)}")
                return False, str(e)
                
            finally:
                # S'assurer que le processus est terminé
                if 'process' in locals():
                    try:
                        process.terminate()
                    except:
                        pass
                
        except Exception as e:
            logger.exception("Exception lors de la création du volume")
            return False, f"Erreur : {str(e)}"
            
    @staticmethod
    def change_password(
        volume_path: str,
        current_password: str,
        new_password: str,
        current_keyfile: str = None,
        new_keyfile: str = None
    ) -> Tuple[bool, str]:
        """Change le mot de passe d'un volume VeraCrypt existant.
        
        Args:
            volume_path: Chemin vers le volume
            current_password: Mot de passe actuel
            new_password: Nouveau mot de passe
            current_keyfile: Fichier clé actuel (optionnel)
            new_keyfile: Nouveau fichier clé (optionnel)
            
        Returns:
            Tuple[bool, str]: (Succès, Message)
        """
        try:
            # Vérifier que le volume existe
            if not os.path.exists(volume_path):
                logger.error(f"Le volume n'existe pas : {volume_path}")
                return False, "Le volume spécifié n'existe pas"
                
            # Construire la commande
            command = [
                'veracrypt',
                '--text',  # Mode texte
                '--non-interactive',  # Mode non interactif
                '--password', current_password,
                '--new-password', new_password,
                '--change',  # Mode changement de mot de passe
                volume_path
            ]
            
            # Ajouter les fichiers clés si spécifiés
            if current_keyfile:
                command.extend(['--keyfile', current_keyfile])
            if new_keyfile:
                command.extend(['--new-keyfile', new_keyfile])
                
            # Exécuter la commande avec sudo
            process = subprocess.Popen(
                ['sudo', '-S'] + command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Récupérer et envoyer le mot de passe sudo
            sudo_password = sudo_session.get_sudo_password()
            if not sudo_password:
                logger.error("Mot de passe sudo non disponible")
                return False, "Mot de passe sudo non disponible"
                
            try:
                stdout, stderr = process.communicate(input=f"{sudo_password}\n", timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                logger.error("Timeout lors du changement de mot de passe")
                return False, "L'opération a pris trop de temps"
                
            if process.returncode != 0:
                error_msg = stderr.strip() if stderr else "Erreur inconnue"
                logger.error(f"Erreur lors du changement de mot de passe : {error_msg}")
                return False, f"Erreur : {error_msg}"
                
            logger.info("Mot de passe changé avec succès")
            return True, "Mot de passe modifié avec succès"
            
        except Exception as e:
            logger.exception("Exception lors du changement de mot de passe")
            return False, f"Erreur : {str(e)}"

    @staticmethod
    def _parse_size(size: str) -> int:
        """Parse une taille avec son unité en bytes.
        
        Args:
            size: Taille avec unité (ex: '100M', '1G', '2T')
            
        Returns:
            Taille en bytes
            
        Raises:
            ValueError: Si le format est invalide
        """
        size = size.upper()
        if size.endswith('M'):
            return int(size[:-1]) * 1024 * 1024
        elif size.endswith('G'):
            return int(size[:-1]) * 1024 * 1024 * 1024
        elif size.endswith('T'):
            return int(size[:-1]) * 1024 * 1024 * 1024 * 1024
        else:
            raise ValueError("Format de taille invalide. Utilisez M, G ou T comme unité")
