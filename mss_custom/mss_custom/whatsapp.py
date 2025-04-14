import frappe
from frappe import _

def get_attachments(message_name):
    """Get attachments for a WhatsApp message.
    
    Args:
        message_name (str): Name of the WhatsApp Message document
        
    Returns:
        list: List of attachment dictionaries with url, name, and type
    """
    attachments = frappe.get_all(
        "File",
        filters={"attached_to_doctype": "WhatsApp Message", "attached_to_name": message_name},
        fields=["file_url", "file_name", "file_type"]
    )
    return [
        {
            'url': frappe.utils.get_url(attachment['file_url']),
            'name': attachment['file_name'],
            'type': attachment['file_type']
        }
        for attachment in attachments
    ]

@frappe.whitelist()
def get_contact_name(phone_number):
    """Get the contact name for a given phone number from WhatsApp Contact doctype.
    
    Args:
        phone_number (str): The phone number to look up
        
    Returns:
        str: The contact name if found, otherwise the phone number
    """
    try:
        contact = frappe.get_doc("WhatsApp Contact", {"mobile_no": phone_number})
        return contact.contact_name
    except frappe.DoesNotExistError:
        return phone_number

@frappe.whitelist()
def get_whatsapp_messages(issue_name):
    """Get raw WhatsApp messages for real-time display in the Issue form.
    
    Args:
        issue_name (str): Name of the Issue document
        
    Returns:
        list: List of message dictionaries
    """
    messages = frappe.get_all(
        "WhatsApp Message",
        filters={
            "reference_doctype": "Issue",
            "reference_name": issue_name
        },
        fields=["name", "type", "message", "creation", "from", "to", "content_type"],
        order_by="creation asc"
    )
    return messages