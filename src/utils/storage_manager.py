import __main__, json, os, tempfile, requests, sys
from typing import Optional, Dict, List
from cryptography.fernet import Fernet

class StorageManager:
    def __init__(self):
        try:
            self._paths = {}
            self._temp_files = []
            
            if getattr(sys, 'frozen', False):
                self._paths["executable"] = os.path.dirname(sys.executable)
                
                if os.path.exists(os.path.join(self._paths["executable"], "lib")):
                    self._paths["base"] = os.path.join(self._paths["executable"], "lib")
                elif os.path.exists(os.path.join(self._paths["executable"], "_internal")):
                    self._paths["base"] = os.path.join(self._paths["executable"], "_internal")
                else:
                    self._paths["base"] = self._paths["executable"]
            else:
                self._paths["executable"] = os.path.dirname(os.path.realpath(__main__.__file__))
                self._paths["base"] = self._paths["executable"]
            
            self._paths["temp"] = tempfile.gettempdir()
        except Exception as e:
            print(f"StorageManager initialization error: {e}")
            raise
    
    def get_executable_path(self) -> str:
        return self._paths["executable"]
    
    def get_base_path(self) -> str:
        return self._paths["base"]
    
    def _verify_and_merge_config(self, original: Optional[Dict], new_data: Optional[Dict]) -> Dict:
        original = original if isinstance(original, dict) else {}
        new_data = new_data if isinstance(new_data, dict) else {}

        config = {}
        for k, v in original.items():
            if isinstance(v, dict):
                config[k] = {
                    subk: new_data.get(k, {}).get(subk, subv)
                    for subk, subv in v.items()
                }
            else:
                config[k] = new_data.get(k, v)
        return config
    
    def _generate_key(self, path_root: str = "base", sub_path: str = "save") -> None:
        save_path = self.get_path(path_root, sub_path)
        if not save_path:
            raise ValueError("Invalid path for key generation.")
        
        os.makedirs(save_path, exist_ok=True)
        key_path = os.path.join(save_path, "secret.key")
        with open(key_path, "wb") as f:
            f.write(Fernet.generate_key())

    def _load_key(self, path_root: str = "base", sub_path: str = "save") -> Optional[bytes]:
        key_path = self.get_path(path_root, os.path.join(sub_path, "secret.key"))
        if key_path and os.path.isfile(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        return None
    
    def get_path(self, path_root: str = "base", relative_path: Optional[str] = None) -> Optional[str]:
        if not relative_path:
            return None
        
        root = self._paths.get(path_root.lower())
        if not root:
            return None
        
        return os.path.join(root, relative_path.replace("/", os.sep).replace("\\", os.sep))
    
    def get_existing_path(self, path_root: str = "base", relative_path: Optional[str] = None) -> Optional[str]:
        full_path = self.get_path(path_root, relative_path)
        return full_path if full_path and os.path.exists(full_path) else None
    
    def save_config(self, path_root: str = "base", sub_path: str = "save", new: Optional[Dict] = None, original: Optional[Dict] = None) -> None:
        try:
            save_path = self.get_path(path_root, sub_path)
            if not save_path:
                raise ValueError("Invalid save path.")

            os.makedirs(save_path, exist_ok=True)

            key = self._load_key(path_root, sub_path)
            if not key:
                self._generate_key(path_root, sub_path)
                key = self._load_key(path_root, sub_path)
                if not key:
                    raise ValueError("Could not load encryption key.")

            data_to_save = self._verify_and_merge_config(original, new)
            encrypted_data = Fernet(key).encrypt(json.dumps(data_to_save).encode("utf-8"))

            config_path = os.path.join(save_path, "config.enc")
            with open(config_path, "wb") as f:
                f.write(encrypted_data)

            print("Successfully saved config.")
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_config(self, path_root: str = "base", sub_path: str = "save", original: Optional[Dict] = None) -> Dict:
        try:
            save_path = self.get_path(path_root, sub_path)
            if not save_path:
                raise ValueError("Invalid save path.")

            key = self._load_key(path_root, sub_path)
            config_path = os.path.join(save_path, "config.enc")

            if not key or not os.path.exists(config_path):
                print("Config not found or key missing.")
                return original or {}

            with open(config_path, "rb") as f:
                decrypted = Fernet(key).decrypt(f.read())

            data = json.loads(decrypted.decode("utf-8"))
            if not isinstance(data, dict):
                print("Decrypted config is not a dictionary.")
                return original or {}

            print("Successfully loaded config.")
            return self._verify_and_merge_config(original, data)
        except Exception as e:
            print(f"Error loading config: {e}")
            return original or {}
    
    def delete_file(self, path_root: str = "base", relative_path: Optional[str] = None) -> bool:
        try:
            if not relative_path:
                return False
            
            file_path = self.get_path(path_root, relative_path)
            if file_path and os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
                
                if path_root.lower() == "temp":
                    name = os.path.basename(file_path)
                    if name in self._temp_files:
                        self._temp_files.remove(name)
                
                return True
            
            print(f"File does not exist: {file_path}")
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def create_temp_txt(self, content: str = "") -> str:
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', dir=self._paths["temp"])
            temp_file.write(content)
            temp_file.close()
            
            self._temp_files.append(os.path.basename(temp_file.name))
            print(f"Created temp file: {temp_file.name}")
            return temp_file.name
        except Exception as e:
            print(f"Error creating temp file: {e}")
            return ""
    
    def get_temp_files(self) -> List[str]:
        return self._temp_files
    
    def get_last_temp_file(self) -> Optional[str]:
        return self._temp_files[-1] if self._temp_files else None
    
    def get_latest_version(self) -> Optional[str]:
        try:
            url = "https://raw.githubusercontent.com/LyubomirT/intense-rp-api-improvements/main/version.txt"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except requests.RequestException as e:
            print(f"Version check failed: {e}")
            return None

        return None