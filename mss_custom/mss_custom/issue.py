# mss_custom/mss_custom/issue.py

import frappe
from frappe.utils import format_datetime, get_datetime, now

def before_print_issue(self, method, args=None):
    """Generate HTML for WhatsApp messages, communications, and comments."""
    # Generate WhatsApp messages HTML
    whatsapp_messages_html = generate_whatsapp_messages_html(self.name)
    
    # Generate communications and comments HTML
    activity_timeline_html = generate_activity_timeline_html(self.doctype, self.name)
    
    # Combine all HTML content with clear section separation
    combined_html = f"""
    <div class="mss-custom-print-wrapper">
        <style>
            .mss-custom-print-wrapper {{
                width: 100%;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                box-sizing: border-box;
            }}
            .mss-custom-section {{
                margin-bottom: 40px;
                break-inside: avoid;
                page-break-inside: avoid;
            }}
            .mss-custom-section-title {{
                font-size: 16px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            }}
            @media print {{
                .mss-custom-print-wrapper {{
                    width: 100% !important;
                    max-width: 100% !important;
                    margin: 0 !important;
                    padding: 20px !important;
                }}
                .mss-custom-section {{
                    margin-bottom: 40px !important;
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                }}
            }}
        </style>
        
        <div class="mss-custom-section">
            <div class="mss-custom-section-title">WhatsApp Messages</div>
        {whatsapp_messages_html}
    </div>
        
        <div class="mss-custom-section">
            <div class="mss-custom-section-title">Activity Timeline</div>
        {activity_timeline_html}
        </div>
    </div>
    """
    
    # Set the combined HTML to the custom field
    self.custom_print_activity_timeline = combined_html

def generate_whatsapp_messages_html(issue_name):
    """Generate HTML for WhatsApp messages in print format."""
    try:
        # Get all WhatsApp messages for this issue
        messages = frappe.get_all("WhatsApp Message",
            filters={"reference_doctype": "Issue", "reference_name": issue_name},
            fields=["name", "message", "type", "creation", "from", "to", "content_type", "owner"]
        )
        
        if not messages:
            return ""
        
        # Group messages by contact
        contact_messages = {}
        for msg in messages:
            contact = msg.get('type') == "Incoming" and msg.get('from') or msg.get('to')
            if contact not in contact_messages:
                contact_messages[contact] = []
            contact_messages[contact].append(msg)
        
        # Sort contacts alphabetically
        sorted_contacts = sorted(contact_messages.keys())
        
        # Debug: Log number of contacts and messages
        frappe.log_error(f"Number of contacts: {len(sorted_contacts)}", "WhatsApp Messages Debug")
        for contact in sorted_contacts:
            frappe.log_error(f"Contact {contact} has {len(contact_messages[contact])} messages", "WhatsApp Messages Debug")
        
        # Start building HTML
        html = """
        <div class="mss-custom-print-wrapper" style="width: 100%; margin: 0; padding: 0;">
            <style>
                .mss-custom-print-wrapper {
                    width: 100%;
                    margin: 0;
                    padding: 0;
                }
                .mss-custom-whatsapp-timeline {
                    width: 100%;
                    margin: 0;
                    padding: 0;
                    display: block;
                }
                .mss-custom-chats-container {
                    width: 100%;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                    align-items: flex-start;
                }
                .mss-custom-chat-section {
                    width: 28%;
                    min-width: 200px;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 8px;
                    background: #ffffff;
                    margin-bottom: 10px;
                    break-inside: avoid;
                    page-break-inside: avoid;
                    box-sizing: border-box;
                    float: left;
                    margin-right: 1%;
                }
                .mss-custom-chat-section:nth-child(3n) {
                    margin-right: 0;
                }
                .mss-custom-contact-header {
                    margin-bottom: 8px;
                    padding-bottom: 6px;
                    border-bottom: 1px solid #e0e0e0;
                }
                .mss-custom-contact-header h3 {
                    margin: 0;
                    color: #333333;
                    font-size: 12px;
                }
                .mss-custom-contact-number {
                    font-size: 10px;
                    color: #666666;
                    display: block;
                }
                .mss-custom-timeline {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                }
                .mss-custom-timeline-item {
                    display: flex;
                    position: relative;
                    margin-bottom: 4px;
                }
                .mss-custom-message-sent {
                    background-color: #f1f1f1;
                    color: #333333;
                    padding: 6px 8px;
                    border-radius: 6px 6px 0 6px;
                    max-width: 80%;
                    margin-right: auto;
                    word-wrap: break-word;
                    font-size: 10px;
                    line-height: 1.3;
                    text-align: left;
                }
                .mss-custom-message-received {
                    background-color: #daf8cb;
                    color: #333333;
                    padding: 6px 8px;
                    border-radius: 6px 6px 6px 0;
                    max-width: 80%;
                    margin-left: auto;
                    word-wrap: break-word;
                    font-size: 10px;
                    line-height: 1.3;
                    text-align: left;
                }
                .mss-custom-message-sent-timestamp,
                .mss-custom-message-received-timestamp {
                    font-size: 6px !important;
                    color: #666666;
                    margin-top: 2px;
                }
                .mss-custom-message-sent-timestamp {
                    text-align: left;
                }
                .mss-custom-message-received-timestamp {
                    text-align: right;
                }
                .mss-custom-message-owner {
                    font-size: 8px;
                    color: #999999;
                    margin-top: 1px;
                    text-align: left;
                    font-style: italic;
                }
                .mss-custom-message-content {
                    margin: 0;
                    padding: 0;
                    text-align: left;
                }
                @media print {
                    .mss-custom-print-wrapper {
                        width: 100% !important;
                        margin: 0 !important;
                        padding: 0 !important;
                    }
                    .mss-custom-whatsapp-timeline {
                        width: 100% !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        display: block !important;
                    }
                    .mss-custom-chats-container {
                        width: 100% !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        display: block !important;
                        overflow: hidden !important;
                    }
                    .mss-custom-chat-section {
                        width: 28% !important;
                        min-width: 200px !important;
                        float: left !important;
                        margin-right: 1% !important;
                        margin-bottom: 10px !important;
                        break-inside: avoid !important;
                        page-break-inside: avoid !important;
                    }
                    .mss-custom-chat-section:nth-child(3n) {
                        margin-right: 0 !important;
                    }
                }
            </style>
            <div class="mss-custom-whatsapp-timeline">
                <div class="mss-custom-chats-container">
        """
        
        # Add chat sections for each contact
        for contact in sorted_contacts:
            msgs = contact_messages[contact]
            # Sort messages by creation time
            msgs.sort(key=lambda x: x.creation)
            
            # Get contact name
            contact_name = frappe.get_value("WhatsApp Contact", {"mobile_no": contact}, "contact_name") or contact
            
            html += f"""
                    <div class="mss-custom-chat-section">
                        <div class="mss-custom-contact-header">
                            <h3>{frappe.utils.escape_html(contact_name)}</h3>
                            <span class="mss-custom-contact-number">{frappe.utils.escape_html(contact)}</span>
                        </div>
                        <div class="mss-custom-timeline">
            """
            
            for msg in msgs:
                msg_class = "mss-custom-message-received" if msg.get('type') == "Incoming" else "mss-custom-message-sent"
                timestamp = frappe.utils.format_datetime(msg.creation)
                
                if msg.content_type == "text":
                    message_content = frappe.utils.escape_html(msg.message or '')
                else:
                    message_content = ''
                    if msg.message:
                        try:
                            message_content = f'<a href="{msg.message}" target="_blank">{msg.message.split("/")[-1]}</a>'
                        except (AttributeError, IndexError):
                            message_content = f'<a href="{msg.message}" target="_blank">File</a>'
                
                # Add owner info for outgoing messages
                owner_info = ""
                if msg.get('type') != "Incoming" and msg.get('owner'):
                    owner_info = f'<div class="mss-custom-message-owner">{frappe.utils.escape_html(msg.owner)}</div>'
                
                html += f"""
                        <div class="mss-custom-timeline-item">
                            <div class="{msg_class}">
                                <div class="mss-custom-message-content">
                                    {message_content}
                                </div>
                                <div class="mss-custom-message-{msg.get('type') == 'Incoming' and 'received' or 'sent'}-timestamp">{timestamp}</div>
                                {owner_info}
                            </div>
                        </div>
                """
            
            html += """
                        </div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        # Debug: Log the generated HTML structure
        frappe.log_error(f"Generated HTML structure: {html[:500]}...", "WhatsApp Messages Debug")
        
        return html
        
    except Exception as e:
        frappe.log_error(f"Error generating WhatsApp messages HTML: {str(e)}", "WhatsApp Messages Error")
        return ""

def generate_activity_timeline_html(doctype, docname):
    """Generate HTML for communications and comments."""
    # Get communications
    communications = frappe.get_all(
        "Communication",
        fields=["subject", "content", "creation", "communication_type", "sender", "reference_doctype", "reference_name", "recipients", "owner"],
        filters={"reference_doctype": doctype, "reference_name": docname},
        order_by="creation desc"
    )
    
    # Get comments (only Comment type)
    comments = frappe.get_all(
        "Comment",
        fields=["comment_by", "content", "creation", "reference_doctype", "reference_name", "comment_type"],
        filters={
            "reference_doctype": doctype, 
            "reference_name": docname,
            "comment_type": "Comment"
        },
        order_by="creation desc"
    )
    
    # # Get document shares
    # shares = frappe.get_all(
    #     "DocShare",
    #     fields=["user", "share_doctype", "share_name", "creation", "share_name"],
    #     filters={"share_doctype": doctype, "share_name": docname},
    #     order_by="creation desc"
    # )
    
    # # Get document assignments
    # assignments = frappe.get_all(
    #     "ToDo",
    #     fields=["allocated_to", "description", "creation", "reference_type", "reference_name", "status"],
    #     filters={"reference_type": doctype, "reference_name": docname},
    #     order_by="creation desc"
    # )
    
    all_activities = []
    
    # Process communications
    for comm in communications:
        if comm.content or comm.subject:
            all_activities.append({
                "type": "communication",
                        "content": comm.content or "",
                        "subject": comm.subject or "",
                "creation": comm.creation,
                        "by": comm.sender,
                        "recipients": comm.recipients,
                        "communication_type": comm.communication_type,
                        "owner": comm.owner
            })
    
    # Process comments
    for comment in comments:
        if comment.content:
            all_activities.append({
                "type": "comment",
                "content": comment.content,
                "creation": comment.creation,
                "by": comment.comment_by
            })
    
    # # Process shares
    # for share in shares:
    #     all_activities.append({
    #         "type": "share",
    #         "content": f"System shared this document with {share.user}",
    #         "creation": share.creation,
    #         "by": "System"
    #     })
    
    # # Process assignments
    # for assignment in assignments:
    #     if assignment.get('status') == "Open":
    #         all_activities.append({
    #             "type": "assignment",
    #             "content": f"System assigned {assignment.allocated_to}: {assignment.description}",
    #             "creation": assignment.creation,
    #             "by": "System"
    #         })
    #     elif assignment.get('status') == "Cancelled":
    #         all_activities.append({
    #             "type": "assignment",
    #             "content": f"Assignment of {assignment.allocated_to} removed by System",
    #             "creation": assignment.creation,
    #             "by": "System"
    #         })
    
    # Sort all activities by creation time
    all_activities.sort(key=lambda x: x['creation'], reverse=True)
    
    # Start building HTML with styling
    html = """
    <div class="mss-custom-activity-timeline">
        <style>
            .mss-custom-activity-timeline {
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                padding: 0;
            }
            .mss-custom-activity-item {
                padding: 8px 0;
                border-bottom: 1px solid #e0e0e0;
                margin-bottom: 0;
                break-inside: avoid;
                page-break-inside: avoid;
            }
            .mss-custom-activity-item:last-child {
                border-bottom: none;
            }
            .mss-custom-activity-type {
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
                color: #666666;
                margin-bottom: 4px;
            }
            .mss-custom-email-block {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                margin: 4px 0;
                max-width: 100%;
                box-sizing: border-box;
            }
            .mss-custom-email-header {
                margin-bottom: 4px;
                padding-bottom: 4px;
                border-bottom: 1px solid #e0e0e0;
            }
            .mss-custom-email-subject {
                font-weight: bold;
                font-size: 12px;
                color: #333333;
                margin-bottom: 4px;
            }
            .mss-custom-email-meta {
                font-size: 11px;
                color: #666666;
            }
            .mss-custom-email-content {
                color: #333333;
                line-height: 1.4;
                font-size: 12px;
                white-space: pre-line;
                margin: 0;
                padding: 0;
            }
            .mss-custom-email-owner {
                font-size: 9px;
                color: #999999;
                margin-top: 2px;
                text-align: right;
                font-style: italic;
            }
            .mss-custom-email-timestamp {
                font-size: 9px;
                color: #666666;
                margin-top: 4px;
                text-align: right;
            }
            .mss-custom-comment-block {
                background-color: #f0f7ff;
                border: 1px solid #d0e3ff;
                border-radius: 4px;
                padding: 8px;
                margin: 4px 0;
                max-width: 100%;
                box-sizing: border-box;
            }
            .mss-custom-comment-author {
                font-weight: bold;
                font-size: 12px;
                color: #2e5ea5;
                margin-bottom: 4px;
            }
            .mss-custom-comment-content {
                color: #333333;
                line-height: 1.4;
                font-size: 12px;
                white-space: pre-line;
                margin: 0;
                padding: 0;
            }
            .mss-custom-comment-timestamp {
                font-size: 9px;
                color: #666666;
                margin-top: 4px;
                text-align: right;
            }
            .mss-custom-system-block {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                margin: 4px 0;
                max-width: 100%;
                box-sizing: border-box;
            }
            .mss-custom-system-content {
                color: #666666;
                line-height: 1.4;
                font-size: 12px;
            }
            .mss-custom-system-timestamp {
                font-size: 9px;
                color: #666666;
                margin-top: 4px;
                text-align: right;
            }
            @media print {
                .mss-custom-activity-timeline {
                    width: 100% !important;
                    max-width: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                .mss-custom-activity-item {
                    padding: 8px 0 !important;
                    border-bottom: 1px solid #e0e0e0 !important;
                    margin-bottom: 0 !important;
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                }
                .mss-custom-email-block,
                .mss-custom-comment-block,
                .mss-custom-system-block {
                    max-width: 100% !important;
                    box-sizing: border-box !important;
                    padding: 8px !important;
                    margin: 4px 0 !important;
                }
            }
        </style>
    """
    
    # Add activity items
    for activity in all_activities:
        if activity['type'] == "communication":
            # Clean HTML content and normalize whitespace
            content = activity["content"]
            if content:
                content = frappe.utils.strip_html(content)
                # Normalize whitespace
                content = ' '.join(content.split())
            
            # Add owner info for outgoing communications
            owner_info = ""
            if activity.get('owner'):
                owner_info = f'<div class="mss-custom-email-owner">Sent by: {frappe.utils.escape_html(activity["owner"])}</div>'
            
            html += f"""
            <div class="mss-custom-activity-item">
                <div class="mss-custom-activity-type">Email</div>
                <div class="mss-custom-email-block">
                    <div class="mss-custom-email-header">
                        {f'<div class="mss-custom-email-subject">{frappe.utils.escape_html(activity["subject"])}</div>' if activity["subject"] else ''}
                        <div class="mss-custom-email-meta">
                            From: {frappe.utils.escape_html(activity["by"])}<br>
                            To: {frappe.utils.escape_html(activity["recipients"] or "N/A")}
                        </div>
                    </div>
                    <div class="mss-custom-email-content">
                        {frappe.utils.escape_html(content)}
                    </div>
                    {owner_info}
                    <div class="mss-custom-email-timestamp">
                        {frappe.utils.format_datetime(activity["creation"])}
                    </div>
                </div>
            </div>
            """
        elif activity['type'] == "comment":
            # Clean HTML content and normalize whitespace
            content = activity["content"]
            if content:
                content = frappe.utils.strip_html(content)
                # Normalize whitespace
                content = ' '.join(content.split())
            
            html += f"""
            <div class="mss-custom-activity-item">
                <div class="mss-custom-activity-type">Comment</div>
                <div class="mss-custom-comment-block">
                    <div class="mss-custom-comment-author">
                        {frappe.utils.escape_html(activity["by"])}
                    </div>
                    <div class="mss-custom-comment-content">
                        {frappe.utils.escape_html(content)}
                    </div>
                    <div class="mss-custom-comment-timestamp">
                        {frappe.utils.format_datetime(activity["creation"])}
                    </div>
                </div>
            </div>
            """
        else:
            # For system messages (shares and assignments)
            html += f"""
            <div class="mss-custom-activity-item">
                <div class="mss-custom-activity-type">System</div>
                <div class="mss-custom-system-block">
                    <div class="mss-custom-system-content">
                        {frappe.utils.escape_html(activity["content"])}
                    </div>
                    <div class="mss-custom-system-timestamp">
                        {frappe.utils.format_datetime(activity["creation"])}
                    </div>
                </div>
            </div>
            """
    
    html += """
    </div>
    """
    
    return html

def update_resolution_details(self):
    """Update resolution details."""
    previous_self = self.get_doc_before_save()

    if not previous_self:
        return

    if previous_self.get('status') != "Closed" and self.get('status') == "Closed":
        time_now = get_datetime(now())
        self.resolution_date = time_now
        if self.opening_date and self.opening_time and self.resolution_date:
            time_var = (time_now - get_datetime(self.creation)).total_seconds()
            self.resolution_time = f"{time_var:.2f}"
        self.save()

def handle_issue_updates(self, method):
    """Handle issue updates."""
    update_resolution_details(self)