# mss_custom/mss_custom/issue.py

import frappe
from frappe.utils import format_datetime

def before_print_issue(self, method, args=None):
    """Generate HTML for WhatsApp messages, communications, and comments."""
    # Generate WhatsApp messages HTML
    whatsapp_messages_html = generate_whatsapp_messages_html(self.name)
    
    # Generate communications and comments HTML
    activity_timeline_html = generate_activity_timeline_html(self.doctype, self.name)
    
    # Combine all HTML content
    combined_html = f"""
    <div class="whatsapp-messages-print">
        {whatsapp_messages_html}
    </div>
    <div class="activity-timeline">
        {activity_timeline_html}
    </div>
    """
    
    # Set the combined HTML to the custom field
    self.custom_print_activity_timeline = combined_html

def generate_whatsapp_messages_html(issue_name):
    """Generate HTML for WhatsApp messages."""
    # Use the whitelisted function to get messages
    messages = frappe.call("mss_custom.mss_custom.whatsapp.get_whatsapp_messages", issue_name=issue_name)
    
    if not messages:
        return "<p>No WhatsApp messages found.</p>"
    
    # Group messages by contact
    contact_messages = {}
    for msg in messages:
        # Get the correct contact number based on message type
        contact = msg.get('from') if msg.get('type') == "Incoming" else msg.get('to')
        if not contact:  # Skip if no contact number
            continue
            
        if contact not in contact_messages:
            contact_messages[contact] = []
        contact_messages[contact].append(msg)
    
    if not contact_messages:
        return "<p>No valid WhatsApp messages found.</p>"
    
    # Get contact names for all contacts at once to avoid multiple calls
    contact_names = {}
    for contact in contact_messages.keys():
        try:
            contact_names[contact] = frappe.call("mss_custom.mss_custom.whatsapp.get_contact_name", phone_number=contact)
        except frappe.DoesNotExistError:
            contact_names[contact] = contact
    
    # Sort contacts alphabetically by contact name
    sorted_contacts = sorted(
        contact_messages.keys(),
        key=lambda x: frappe.utils.escape_html(contact_names.get(x, x))
    )
    
    # Generate HTML for each contact's messages
    contact_sections = []
    for contact in sorted_contacts:
        msgs = contact_messages[contact]
        contact_name = contact_names.get(contact, contact)
        
        # Sort messages by creation time
        msgs.sort(key=lambda x: x.creation)
        
        timeline_items = []
        for msg in msgs:
            msg_class = "mss-custom-message-received" if msg.type == "Incoming" else "mss-custom-message-sent"
            content = msg.message
            if msg.content_type != "text":
                content = f'<a href="{msg.message}" target="_blank">{msg.message.split("/")[-1]}</a>'
            else:
                content = frappe.utils.escape_html(content)
            
            timestamp = frappe.utils.format_datetime(msg.creation, "HH:mm")
            timeline_items.append(f"""
            <div class="mss-custom-timeline-item" style="display: flex; position: relative; margin-bottom: 5px;">
                <div class="{msg_class}" style="padding: 8px 12px; border-radius: 8px; max-width: 80%; word-wrap: break-word; {'background-color: #daf8cb; color: #333333; border-radius: 8px 8px 0 8px; margin-left: auto;' if msg.type == 'Outgoing' else 'background-color: #f1f1f1; color: #333333; border-radius: 8px 8px 8px 0; margin-right: auto;'}">
                    <p style="margin: 0;">{content}</p>
                    <div class="mss-custom-message-timestamp" style="font-size: 11px; color: #666666; margin-top: 4px; text-align: right;">{timestamp}</div>
                </div>
            </div>
            """)
        
        contact_sections.append(f"""
        <div class="mss-custom-chat-section" style="border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px; background: #ffffff; margin-bottom: 15px;">
            <div class="mss-custom-contact-header" style="margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #e0e0e0;">
                <h3 style="margin: 0; color: #333333; font-size: 14px;">{frappe.utils.escape_html(contact_name)}</h3>
                <span class="mss-custom-contact-number" style="font-size: 12px; color: #666666; display: block;">{frappe.utils.escape_html(contact)}</span>
            </div>
            <div class="mss-custom-timeline" style="display: flex; flex-direction: column; gap: 8px;">
                {''.join(timeline_items)}
            </div>
        </div>
        """)
    
    return f"""
    <div class="mss-custom-whatsapp-timeline" style="margin: 15px 0;">
        <div class="mss-custom-chats-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
            {''.join(contact_sections)}
        </div>
    </div>
    """

def generate_activity_timeline_html(doctype, docname):
    """Generate HTML for communications and comments."""
    communications = frappe.get_all(
        "Communication",
        fields=["subject", "content", "creation", "communication_type", "sender"],
        filters={"reference_doctype": doctype, "reference_name": docname},
        order_by="creation desc"
    )
    
    comments = frappe.get_all(
        "Comment",
        fields=["comment_by", "content", "creation"],
        filters={"reference_doctype": doctype, "reference_name": docname},
        order_by="creation desc"
    )
    
    all_activities = []
    for comm in communications:
        all_activities.append({
            "type": "communication",
            "content": comm.content or "No Content",
            "subject": comm.subject or "No Subject",
            "creation": comm.creation,
            "by": comm.sender
        })
    
    for comment in comments:
        all_activities.append({
            "type": "comment",
            "content": comment.content,
            "creation": comment.creation,
            "by": comment.comment_by
        })
    
    all_activities.sort(key=lambda x: x['creation'], reverse=True)
    
    activity_items = []
    for activity in all_activities:
        if activity['type'] == "communication":
            activity_items.append(f"""
            <div class="activity-item">
                <p><strong>{activity['subject']}</strong></p>
                <p>{activity['content']}</p>
                <p class="activity-meta">{format_datetime(activity['creation'])}</p>
            </div>
            """)
        else:
            activity_items.append(f"""
            <div class="activity-item">
                <p><strong>{activity['by']}</strong> commented:</p>
                <p>{activity['content']}</p>
                <p class="activity-meta">{format_datetime(activity['creation'])}</p>
            </div>
            """)
    
    return ''.join(activity_items)

def get_contact_name(phone_number):
    """Get the contact name for a given phone number."""
    try:
        contact = frappe.get_doc("WhatsApp Contact", {"mobile_no": phone_number})
        return contact.contact_name
    except frappe.DoesNotExistError:
        return phone_number