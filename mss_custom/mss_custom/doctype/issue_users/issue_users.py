import frappe
from frappe import _
import json
from frappe.desk.form import assign_to

def validate_issue_users(doc, method=None):
    """Validate all Issue Users in the Issue document."""
    # Track users to check for duplicates
    users = set()
    
    for user in doc.custom_support_team:
        if user.user:
            # Check for duplicate users
            if user.user in users:
                frappe.throw(_(f"User {user.user} is already added to this Issue"))
            users.add(user.user)
            
            # Check if user exists and is enabled
            user_doc = frappe.get_doc("User", user.user)
            if not user_doc.enabled:
                frappe.throw(_(f"User {user.user} is disabled"))

def handle_issue_users_changes(doc, method=None):
    """Handle changes to Issue Users child table."""
    try:
        if not doc.get_doc_before_save():
            # New document, create assignments for all users
            for user in doc.custom_support_team:
                if user.user:
                    create_user_assignment(doc, user.user, user.type)
            return
        
        # Get current and previous state of users
        current_users = {row.user: row for row in doc.custom_support_team}
        previous_users = {row.user: row for row in doc.get_doc_before_save().custom_support_team}
        
        # Log the current and previous states for debugging
        frappe.log_error(f"Current users: {list(current_users.keys())}", "IssueUsers Debug")
        frappe.log_error(f"Previous users: {list(previous_users.keys())}", "IssueUsers Debug")
        
        # Handle removed users
        removed_users = set(previous_users.keys()) - set(current_users.keys())
        frappe.log_error(f"Removed users: {removed_users}", "IssueUsers Debug")
        for user in removed_users:
            # Get all ToDo references for this user
            todo_refs = frappe.get_all("ToDo", 
                filters={
                    "reference_type": "Issue",
                    "reference_name": doc.name,
                    "allocated_to": user,
                    "status": "Open"
                },
                fields=["name"]
            )
            for todo in todo_refs:
                cancel_user_assignment(doc, user, todo.name)
        
        # Handle new users
        new_users = set(current_users.keys()) - set(previous_users.keys())
        frappe.log_error(f"New users: {new_users}", "IssueUsers Debug")
        for user in new_users:
            create_user_assignment(doc, user, current_users[user].type)
        
        # Handle modified users
        modified_users = set(current_users.keys()) & set(previous_users.keys())
        frappe.log_error(f"Modified users: {modified_users}", "IssueUsers Debug")
        for user in modified_users:
            if current_users[user].type != previous_users[user].type:
                # If type changed, cancel old assignment and create new one
                todo_refs = frappe.get_all("ToDo", 
                    filters={
                        "reference_type": "Issue",
                        "reference_name": doc.name,
                        "allocated_to": user,
                        "status": "Open"
                    },
                    fields=["name"]
                )
                for todo in todo_refs:
                    cancel_user_assignment(doc, user, todo.name)
                create_user_assignment(doc, user, current_users[user].type)
    except Exception as e:
        frappe.log_error(f"Error in handle_issue_users_changes: {str(e)}", "IssueUsers Error")
        raise

def create_user_assignment(doc, user, user_type):
    """Assign the user to the Issue and create notification."""
    try:
        # First check for and clean up any existing assignments
        existing_todos = frappe.get_all("ToDo", 
            filters={
                "reference_type": "Issue",
                "reference_name": doc.name,
                "allocated_to": user,
                "status": "Open"
            },
            fields=["name"]
        )
        
        # Cancel any existing assignments
        for todo in existing_todos:
            cancel_user_assignment(doc, user, todo.name)
        
        # Now create the new assignment
        assign_to.add({
            "assign_to": [user],
            "doctype": "Issue",
            "name": doc.name,
            "description": f"Assigned as {user_type} to Issue: {doc.subject}",
            "subject": f"Assigned as {user_type} to Issue: {doc.subject}",
            "priority": "Medium"
        }, ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Failed to create assignment: {str(e)}", "IssueUsers Error")
        raise

def cancel_user_assignment(doc, user, todo_reference):
    """Remove user assignment from Issue and create notification."""
    try:
        frappe.log_error(f"Removing user {user} from Issue assignments with todo {todo_reference}", "IssueUsers Cancel Assignment")
        # First try to cancel the specific ToDo
        if todo_reference:
            todo = frappe.get_doc("ToDo", todo_reference)
            if todo and todo.status == "Open":
                todo.status = "Cancelled"
                todo.save(ignore_permissions=True)
        
        # Then ensure the user is removed from assignments
        assign_to.remove("Issue", doc.name, user, ignore_permissions=True)
        
        # Double check and remove any remaining open ToDos
        remaining_todos = frappe.get_all("ToDo", 
            filters={
                "reference_type": "Issue",
                "reference_name": doc.name,
                "allocated_to": user,
                "status": "Open"
            },
            fields=["name"]
        )
        for todo in remaining_todos:
            todo_doc = frappe.get_doc("ToDo", todo.name)
            todo_doc.status = "Cancelled"
            todo_doc.save(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(f"Failed to cancel assignment: {str(e)}", "IssueUsers Error")
        raise
