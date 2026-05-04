import os
import json
import hashlib
import tempfile
import shutil

class CheckpointManager:
    def __init__(self, checkpoint_name, source_file_path):
        self.checkpoint_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "DATA", "processed", ".checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.checkpoint_path = os.path.join(self.checkpoint_dir, f"{checkpoint_name}.json")
        self.source_file_path = source_file_path
        self.source_hash = self._get_file_hash(source_file_path)

    def _get_file_hash(self, file_path):
        """Calculates MD5 hash of the source file to detect changes."""
        if not os.path.exists(file_path):
            return None
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def load_checkpoint(self):
        """Loads the checkpoint if it exists and the file hash matches."""
        if not os.path.exists(self.checkpoint_path):
            return 0
        
        try:
            with open(self.checkpoint_path, 'r') as f:
                state = json.load(f)
            
            if state.get("source_hash") == self.source_hash:
                return state.get("last_index", 0)
        except Exception:
            pass
        return 0

    def save_checkpoint(self, last_index):
        """Saves the current progress atomically."""
        state = {
            "source_hash": self.source_hash,
            "last_index": last_index
        }
        
        # Write to temporary file first then rename (atomic)
        with tempfile.NamedTemporaryFile('w', delete=False, dir=self.checkpoint_dir) as tf:
            json.dump(state, tf)
            temp_name = tf.name
        
        shutil.move(temp_name, self.checkpoint_path)

    def reset(self):
        """Removes the checkpoint file."""
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path)
