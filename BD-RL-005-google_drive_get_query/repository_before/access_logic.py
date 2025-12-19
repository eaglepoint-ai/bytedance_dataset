# access_logic.py
from repository_before.models import Folder, File, Permission

PERMISSION_RANK = {
    "view": 1,
    "comment": 2,
    "edit": 3,
    "owner": 4,
}

def build_folder_tree(folders):
    tree = {}
    by_id = {f.id: f for f in folders}

    for folder in folders:
        if folder.parentId:
            tree.setdefault(folder.parentId, []).append(folder)
        else:
            tree.setdefault(None, []).append(folder)

    return tree, by_id

def collect_descendants(folder_id, tree, result):
    children = tree.get(folder_id, [])
    for child in children:
        result.add(child.id)
        collect_descendants(child.id, tree, result)

def get_accessible_resources(session, user_id):
    folders = session.query(Folder).all()
    files = session.query(File).all()
    permissions = session.query(Permission).filter(
        Permission.userId == user_id
    ).all()

    folder_tree, folder_map = build_folder_tree(folders)

    accessible_folders = {}
    accessible_files = {}

    # 1. Ownership
    for f in folders:
        if f.ownerId == user_id:
            accessible_folders[f.id] = "owner"

    for f in files:
        if f.ownerId == user_id:
            accessible_files[f.id] = "owner"

    # 2. Explicit permissions
    for p in permissions:
        if p.resourceType == "folder":
            accessible_folders[p.resourceId] = p.level
        elif p.resourceType == "file":
            accessible_files[p.resourceId] = p.level

    # 3. Folder inheritance (recursive)
    inherited_folder_ids = set()
    for folder_id in list(accessible_folders.keys()):
        collect_descendants(folder_id, folder_tree, inherited_folder_ids)

    for fid in inherited_folder_ids:
        if fid not in accessible_folders:
            accessible_folders[fid] = "view"  # naive inheritance

    # 4. Files inside accessible folders
    for file in files:
        if file.folderId in accessible_folders:
            if file.id not in accessible_files:
                accessible_files[file.id] = accessible_folders[file.folderId]

    return {
        "folders": list(accessible_folders.keys()),
        "files": list(accessible_files.keys()),
    }
