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

@frappe.whitelist()
def get_whatsapp_messages_html_for_print(issue_name):
    """Get WhatsApp messages HTML formatted for print format.
    
    This function is used by the Issue print format to generate a clean,
    print-friendly version of the WhatsApp messages.
    
    Args:
        issue_name (str): Name of the Issue document
        
    Returns:
        str: HTML content for the print format
    """
    messages = get_whatsapp_messages(issue_name)
    
    if not messages:
        return ""
        
    # Group messages by contact
    contact_messages = {}
    for msg in messages:
        contact = msg.from_no if msg.type == "Incoming" else msg.to_no
        if contact not in contact_messages:
            contact_messages[contact] = []
        contact_messages[contact].append(msg)
    
    # Sort contacts alphabetically
    sorted_contacts = sorted(contact_messages.keys())
    
    html = """
    <div class="whatsapp-messages-print">
        <h3>WhatsApp Messages</h3>
    """
    
    for contact in sorted_contacts:
        msgs = contact_messages[contact]
        # Get contact name
        contact_name = get_contact_name(contact)
        
        html += f"""
        <div class="chat-section">
            <div class="contact-header">
                <h4>{frappe.utils.escape_html(contact_name)}</h4>
                <span class="contact-number">{frappe.utils.escape_html(contact)}</span>
            </div>
            <div class="timeline">
        """
        
        # Sort messages by creation time
        msgs.sort(key=lambda x: x.creation)
        
        for msg in msgs:
            msg_class = "message-received" if msg.type == "Incoming" else "message-sent"
            timestamp = frappe.utils.get_datetime(msg.creation).strftime("%Y-%m-%d %H:%M:%S")
            
            if msg.content_type == "text":
                message_content = frappe.utils.escape_html(msg.message)
            else:
                message_content = f'<a href="{msg.message}" target="_blank">{msg.message.split("/")[-1]}</a>'
            
            html += f"""
                <div class="timeline-item">
                    <div class="{msg_class}">
                        <p>{message_content}</p>
                        <div class="timestamp">{timestamp}</div>
                    </div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
    
    html += """
        <style>
            .whatsapp-messages-print {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
            }
            
            .chat-section {
                margin-bottom: 30px;
                page-break-inside: avoid;
            }
            
            .contact-header {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
            }
            
            .contact-header h4 {
                margin: 0;
                color: #333;
            }
            
            .contact-number {
                color: #666;
                font-size: 0.9em;
            }
            
            .timeline {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .timeline-item {
                display: flex;
                flex-direction: column;
                max-width: 70%;
            }
            
            .message-sent {
                align-self: flex-end;
                background-color: #e3f2fd;
                border-radius: 10px 10px 0 10px;
                padding: 10px;
                margin-left: auto;
            }
            
            .message-received {
                align-self: flex-start;
                background-color: #f1f1f1;
                border-radius: 10px 10px 10px 0;
                padding: 10px;
                margin-right: auto;
            }
            
            .timestamp {
                font-size: 0.8em;
                color: #666;
                margin-top: 5px;
                text-align: right;
            }
            
            @media print {
                .whatsapp-messages-print {
                    width: 100%;
                }
                
                .chat-section {
                    break-inside: avoid;
                }
            }
        </style>
    </div>
    """
    
    return html