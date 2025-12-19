# access_logic.py
"""
Optimized access logic for Google Drive-like permission system.

Key optimizations over the naive implementation:
1. Uses recursive CTE for folder hierarchy traversal (database-side, not Python)
2. Single query using UNION to combine all access sources
3. Filters at database level - never loads all folders/files into memory
4. Minimizes round trips to database (2 queries total: folders + files)

This scales to millions of folders/files because the database handles:
- Recursive tree traversal via CTE
- Set operations via UNION
- Filtering via WHERE clauses with indexes
"""

from sqlalchemy import text


def get_accessible_resources(session, user_id):
    """
    Return all folders and files accessible to a user.
    
    Access is granted via:
    1. Ownership (user owns the resource)
    2. Direct permission (permission record for the resource)
    3. Inherited permission (parent folder has permission, applies to descendants)
    
    Uses recursive CTE for efficient hierarchy traversal in the database.
    """
    
    # Query for accessible folders using recursive CTE
    # This finds:
    # 1. Folders owned by user
    # 2. Folders with direct permission
    # 3. All descendant folders of folders with permission (recursive CTE)
    accessible_folders_query = text("""
        WITH RECURSIVE 
        -- Base: folders user has direct access to (owned or permitted)
        direct_access_folders AS (
            -- Folders owned by user
            SELECT id FROM folders WHERE "ownerId" = :user_id
            UNION
            -- Folders with explicit permission
            SELECT p."resourceId" as id 
            FROM permissions p
            WHERE p."userId" = :user_id 
              AND p."resourceType" = 'folder'
              AND EXISTS (SELECT 1 FROM folders f WHERE f.id = p."resourceId")
        ),
        -- Recursive: find all descendant folders
        all_accessible_folders AS (
            -- Start with directly accessible folders
            SELECT id FROM direct_access_folders
            UNION
            -- Recursively add children of accessible folders
            SELECT f.id
            FROM folders f
            INNER JOIN all_accessible_folders aaf ON f."parentId" = aaf.id
        )
        SELECT DISTINCT id FROM all_accessible_folders
    """)
    
    # Query for accessible files
    # This finds:
    # 1. Files owned by user
    # 2. Files with direct permission
    # 3. Files inside any accessible folder
    accessible_files_query = text("""
        WITH RECURSIVE 
        -- Base: folders user has direct access to
        direct_access_folders AS (
            SELECT id FROM folders WHERE "ownerId" = :user_id
            UNION
            SELECT p."resourceId" as id 
            FROM permissions p
            WHERE p."userId" = :user_id 
              AND p."resourceType" = 'folder'
              AND EXISTS (SELECT 1 FROM folders f WHERE f.id = p."resourceId")
        ),
        -- Recursive: all accessible folders including descendants
        all_accessible_folders AS (
            SELECT id FROM direct_access_folders
            UNION
            SELECT f.id
            FROM folders f
            INNER JOIN all_accessible_folders aaf ON f."parentId" = aaf.id
        )
        -- Files accessible to user
        SELECT DISTINCT id FROM (
            -- Files owned by user
            SELECT id FROM files WHERE "ownerId" = :user_id
            UNION
            -- Files with direct permission
            SELECT p."resourceId" as id 
            FROM permissions p
            WHERE p."userId" = :user_id 
              AND p."resourceType" = 'file'
              AND EXISTS (SELECT 1 FROM files f WHERE f.id = p."resourceId")
            UNION
            -- Files inside accessible folders
            SELECT f.id
            FROM files f
            WHERE f."folderId" IN (SELECT id FROM all_accessible_folders)
        ) AS accessible_files
    """)
    
    # Execute queries
    folder_result = session.execute(accessible_folders_query, {"user_id": user_id})
    folder_ids = [row[0] for row in folder_result]
    
    file_result = session.execute(accessible_files_query, {"user_id": user_id})
    file_ids = [row[0] for row in file_result]
    
    return {
        "folders": folder_ids,
        "files": file_ids,
    }


def get_accessible_resources_with_levels(session, user_id):
    """
    Extended version that also returns permission levels.
    
    Useful when you need to know what actions the user can perform
    on each resource (view, comment, edit, owner).
    """
    
    # Query with permission levels
    accessible_folders_with_levels_query = text("""
        WITH RECURSIVE 
        direct_access_folders AS (
            -- Owned folders get 'owner' level
            SELECT id, 'owner' as level FROM folders WHERE "ownerId" = :user_id
            UNION
            -- Permitted folders get their permission level
            SELECT p."resourceId" as id, p.level
            FROM permissions p
            WHERE p."userId" = :user_id 
              AND p."resourceType" = 'folder'
              AND EXISTS (SELECT 1 FROM folders f WHERE f.id = p."resourceId")
        ),
        all_accessible_folders AS (
            SELECT id, level FROM direct_access_folders
            UNION
            -- Inherited folders get 'view' (or could inherit parent's level)
            SELECT f.id, 'view' as level
            FROM folders f
            INNER JOIN all_accessible_folders aaf ON f."parentId" = aaf.id
            WHERE f.id NOT IN (SELECT id FROM direct_access_folders)
        )
        -- Use highest permission level when multiple exist
        SELECT id, MAX(level) as level 
        FROM all_accessible_folders 
        GROUP BY id
    """)
    
    accessible_files_with_levels_query = text("""
        WITH RECURSIVE 
        direct_access_folders AS (
            SELECT id, 'owner' as level FROM folders WHERE "ownerId" = :user_id
            UNION
            SELECT p."resourceId" as id, p.level
            FROM permissions p
            WHERE p."userId" = :user_id 
              AND p."resourceType" = 'folder'
              AND EXISTS (SELECT 1 FROM folders f WHERE f.id = p."resourceId")
        ),
        all_accessible_folders AS (
            SELECT id, level FROM direct_access_folders
            UNION
            SELECT f.id, 'view' as level
            FROM folders f
            INNER JOIN all_accessible_folders aaf ON f."parentId" = aaf.id
            WHERE f.id NOT IN (SELECT id FROM direct_access_folders)
        ),
        folder_levels AS (
            SELECT id, MAX(level) as level FROM all_accessible_folders GROUP BY id
        )
        SELECT id, MAX(level) as level FROM (
            -- Owned files
            SELECT id, 'owner' as level FROM files WHERE "ownerId" = :user_id
            UNION ALL
            -- Directly permitted files
            SELECT p."resourceId" as id, p.level
            FROM permissions p
            WHERE p."userId" = :user_id 
              AND p."resourceType" = 'file'
              AND EXISTS (SELECT 1 FROM files f WHERE f.id = p."resourceId")
            UNION ALL
            -- Files in accessible folders (inherit folder's level)
            SELECT f.id, fl.level
            FROM files f
            INNER JOIN folder_levels fl ON f."folderId" = fl.id
        ) AS all_files
        GROUP BY id
    """)
    
    folder_result = session.execute(accessible_folders_with_levels_query, {"user_id": user_id})
    folders = {row[0]: row[1] for row in folder_result}
    
    file_result = session.execute(accessible_files_with_levels_query, {"user_id": user_id})
    files = {row[0]: row[1] for row in file_result}
    
    return {
        "folders": folders,
        "files": files,
    }

