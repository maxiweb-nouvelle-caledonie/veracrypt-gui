"""
Utilitaires pour la création de volumes VeraCrypt.
"""

import os
import logging
import subprocess
from typing import List, Tuple, Dict, Optional
from .sudo_session import sudo_session

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
        random_data: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Crée un nouveau volume VeraCrypt."""
        try:
            # Log des paramètres (sans les mots de passe)
            logger.info(f"Création d'un volume VeraCrypt :")
            logger.info(f"- Chemin : {path}")
            logger.info(f"- Taille : {size}")
            logger.info(f"- Chiffrement : {encryption}")
            logger.info(f"- Hash : {hash_algo}")
            logger.info(f"- Système de fichiers : {filesystem}")
            logger.info(f"- Volume caché : {hidden}")
            if hidden:
                logger.info(f"- Taille du volume caché : {hidden_size}")
            
            # Construire la commande de base
            cmd = [
                'veracrypt',
                '--text',
                '--create',
                path,
                '--encryption', VolumeCreation.ENCRYPTION_ALGORITHMS[encryption],
                '--hash', VolumeCreation.HASH_ALGORITHMS[hash_algo],
                '--filesystem', VolumeCreation.FILESYSTEMS[filesystem],
                '--size', size,
                '--no-keyfiles',
                '--non-interactive'
            ]
            
            if pim is not None:
                cmd.extend(['--pim', str(pim)])
            else:
                cmd.append('--no-pim')
                
            if hidden:
                if not hidden_size or not hidden_password:
                    logger.error("Taille ou mot de passe manquant pour le volume caché")
                    return False, "Taille et mot de passe requis pour le volume caché"
                    
                cmd.extend(['--hidden', '--hidden-size', hidden_size])
                if hidden_pim is not None:
                    cmd.extend(['--hidden-pim', str(hidden_pim)])
                    
            # Log de la commande (sans les mots de passe)
            log_cmd = cmd.copy()
            logger.info(f"Commande : {' '.join(log_cmd)}")
            
            # Préparer les réponses aux prompts
            responses = []
            
            # Mot de passe principal (deux fois)
            responses.extend([password, password])
            
            # Mot de passe du volume caché (deux fois)
            if hidden:
                responses.extend([hidden_password, hidden_password])
                
            # Données aléatoires si fournies
            if random_data:
                responses.append(random_data)
                
            # Joindre les réponses avec des retours à la ligne
            input_data = '\n'.join(responses) + '\n'
            
            logger.debug(f"Nombre de réponses préparées : {len(responses)}")
            
            # Exécuter la commande avec sudo
            process = subprocess.Popen(
                ['sudo', '-S'] + cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Envoyer le mot de passe sudo
            sudo_password = sudo_session.get_sudo_password()
            if not sudo_password:
                return False, "Mot de passe sudo non disponible"
                
            process.stdin.write(sudo_password + '\n')
            process.stdin.flush()
            
            # Envoyer les réponses à VeraCrypt
            process.stdin.write(input_data)
            process.stdin.flush()
            
            # Attendre la fin de la commande
            stdout, stderr = process.communicate()
            success = process.returncode == 0
            
            if success:
                logger.info("Volume créé avec succès")
                return True, "Volume créé avec succès"
            else:
                logger.error(f"Erreur lors de la création du volume :")
                logger.error(f"Sortie standard : {stdout}")
                logger.error(f"Erreur standard : {stderr}")
                return False, f"Erreur lors de la création du volume : {stderr}"
                
        except Exception as e:
            logger.exception("Exception lors de la création du volume")
            return False, f"Erreur : {str(e)}"
