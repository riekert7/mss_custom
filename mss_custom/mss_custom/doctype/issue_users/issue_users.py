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
    if not doc.get_doc_before_save():
        # New document, create assignments for all users
        for user in doc.custom_support_team:
            if user.user:
                create_user_assignment(doc, user.user, user.type)
        return
    
    # Get current and previous state of users
    current_users = {row.user: row for row in doc.custom_support_team}
    previous_users = {row.user: row for row in doc.get_doc_before_save().custom_support_team}
    
    # Handle removed users
    for user in set(previous_users.keys()) - set(current_users.keys()):
        if previous_users[user].todo_reference:
            cancel_user_assignment(doc, user, previous_users[user].todo_reference)
    
    # Handle new users
    for user in set(current_users.keys()) - set(previous_users.keys()):
        create_user_assignment(doc, user, current_users[user].type)
    
    # Handle modified users
    for user in set(current_users.keys()) & set(previous_users.keys()):
        if current_users[user].type != previous_users[user].type:
            # If type changed, cancel old assignment and create new one
            if previous_users[user].todo_reference:
                cancel_user_assignment(doc, user, previous_users[user].todo_reference)
            create_user_assignment(doc, user, current_users[user].type)

def create_user_assignment(doc, user, user_type):
    """Assign the user to the Issue and create notification."""
    try:
        # Use Frappe's assign_to module to handle the assignment
        assign_to.add({
            "assign_to": [user],
            "doctype": "Issue",
            "name": doc.name,
            "description": f"Assigned as {user_type} to Issue: {doc.subject}",
            "priority": "Medium"
        }, ignore_permissions=True)
    except Exception as e:
        frappe.throw(_(f"Failed to create assignment: {str(e)}"))

def cancel_user_assignment(doc, user, todo_reference):
    """Remove user assignment from Issue and create notification."""
    try:
        # Use Frappe's assign_to module to handle the unassignment
        assign_to.remove("Issue", doc.name, user, ignore_permissions=True)
    except Exception as e:
        frappe.throw(_(f"Failed to cancel assignment: {str(e)}"))
