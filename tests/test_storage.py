from core.nexusmind.storage.local_storage import LocalStorage
import pytest


def test_save_and_exists(tmp_path):
    """
    Test saving a file and checking its existence.
    """
    storage = LocalStorage(base_path=str(tmp_path))
    file_path = "test_dir/test_file.txt"
    content = b"Hello, World!"

    assert not storage.exists(file_path)
    storage.save(file_path, content)
    assert storage.exists(file_path)


def test_get_content(tmp_path):
    """
    Test getting the content of a saved file.
    """
    storage = LocalStorage(base_path=str(tmp_path))
    file_path = "test_file.txt"
    content = b"Hello, again!"

    storage.save(file_path, content)
    retrieved_content = storage.get(file_path)
    assert retrieved_content == content


def test_delete_file(tmp_path):
    """
    Test deleting a file.
    """
    storage = LocalStorage(base_path=str(tmp_path))
    file_path = "file_to_delete.txt"
    content = b"Delete me."

    storage.save(file_path, content)
    assert storage.exists(file_path)

    storage.delete(file_path)
    assert not storage.exists(file_path)


def test_get_non_existent_file(tmp_path):
    """
    Test that getting a non-existent file raises an error.
    """
    storage = LocalStorage(base_path=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        storage.get("non_existent_file.txt")


def test_delete_non_existent_file(tmp_path):
    """
    Test that deleting a non-existent file does not raise an error.
    """
    storage = LocalStorage(base_path=str(tmp_path))
    try:
        storage.delete("non_existent_file.txt")
    except Exception as e:
        pytest.fail(f"Deleting a non-existent file raised an exception: {e}") 