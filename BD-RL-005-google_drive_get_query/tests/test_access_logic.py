"""Tests for access logic - verifying users see correct resources."""


def test_user_sees_owned_resources(client):
    """Test that a user can see resources they own."""
    res = client.get("/dashboard/user_1").json
    assert "folder_1" in res["folders"], f"Expected folder_1 in {res['folders']}"
    assert "file_1" in res["files"], f"Expected file_1 in {res['files']}"


def test_folder_permission_includes_descendants(client):
    """Test that folder permission grants access to child folders and files."""
    res = client.get("/dashboard/user_2").json
    # user_2 has permission to parent_folder, should see child_folder and its files
    assert "child_folder" in res["folders"], f"Expected child_folder in {res['folders']}"
    assert "file_inside_child" in res["files"], f"Expected file_inside_child in {res['files']}"


def test_direct_file_permission_works(client):
    """Test that direct file permission grants access to that file."""
    res = client.get("/dashboard/user_3").json
    # user_3 has direct permission to shared_file
    assert "shared_file" in res["files"], f"Expected shared_file in {res['files']}"


def test_no_duplicate_resources(client):
    """Test that resources are not duplicated in the response."""
    res = client.get("/dashboard/user_1").json
    
    # Check no duplicate folders
    assert len(res["folders"]) == len(set(res["folders"])), "Duplicate folders found"
    
    # Check no duplicate files  
    assert len(res["files"]) == len(set(res["files"])), "Duplicate files found"


def test_empty_user_gets_empty_response(client):
    """Test that a user with no resources gets empty lists."""
    res = client.get("/dashboard/nonexistent_user").json
    assert res["folders"] == [], f"Expected empty folders, got {res['folders']}"
    assert res["files"] == [], f"Expected empty files, got {res['files']}"
