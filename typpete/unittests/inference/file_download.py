"""Mocking built in function urlretrieve and built-in library os

Remove when their stubs are implemented
"""


def urlretrieve(download_path: str, local_path: str) -> None:
    pass


class Path:
    def dirname(self, path: str) -> str:
        return path


class OS:
    path = Path()

    def makedirs(self, dirname: str, exist_ok: bool):
        pass


os = OS()


class File:
    def __init__(self, local_path, download_path, file_name):
        self.local_path = local_path
        self.download_path = download_path
        self.file_name = file_name

    def download(self):
        self.create_folder_if_not_exists()
        urlretrieve(self.download_path, self.local_path)
        print("Downloaded: " + self.local_path)
        return True

    def create_folder_if_not_exists(self):
        """Create new folder(s) in the local path"""
        os.makedirs(os.path.dirname(self.local_path), True)

f1 = File("home/user", "http://www.download.com/", "file.py")
ch1 = f1.download()

f2 = File(f1.local_path, f1.download_path + "2", "file2.py")
ch2 = f2.download()

if ch1 and ch2:
    print("DONE!")

# File := Type[File]
# f1 := File
# f2 := File
# ch1 := bool
# ch2 := bool
