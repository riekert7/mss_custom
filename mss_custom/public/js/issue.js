$(document).on('app_ready', function () {
    frappe.router.on("change", () => {
        var route = frappe.get_route();
        if (route && route[0] == "Form" && route[1] == "Issue") {
            frappe.ui.form.on("Issue", {
                refresh: function(frm) {
                    // Add a custom section for messages
                    if (!frm.custom_messages_section) {
                        // Create a new section
                        frm.custom_messages_section = $(`
                            <div class="section issue-form">
                                <div class="section-head">
                                <h3></h3>    
                                <h3>WhatsApp Chats on Ticket</h3>
                                </div>
                                <div class="section-body">
                                    <div class="mss-custom-whatsapp-timeline">
                                        <div class="mss-custom-chats-container"></div>
                                    </div>
                                </div>
                            </div>
                        `);
                        
                        // Add the section to the form's main content area
                        frm.page.wrapper.find('.form-layout').append(frm.custom_messages_section);
                    }
                    
                    // Initial load of messages
                    load_messages(frm);
                    
                    // Subscribe to real-time updates
                    subscribe_to_updates(frm);
                }
            });

            // Add validation for Issue Users child table
            frappe.ui.form.on("Issue Users", {
                user: function(frm, cdt, cdn) {
                    let row = locals[cdt][cdn];
                    if (!row.user) return;

                    // Check for duplicate users in the table
                    let duplicate = frm.doc.custom_support_team.filter(d => 
                        d.user === row.user && d.name !== row.name
                    );

                    if (duplicate.length > 0) {
                        frappe.throw(__("User {0} is already added to this Issue", [row.user]));
                        frappe.model.set_value(cdt, cdn, 'user', '');
                    }
                }
            });
        }
    });
});

function load_messages(frm) {
    frappe.call({
        method: 'mss_custom.mss_custom.whatsapp.get_whatsapp_messages',
        args: {
            issue_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                update_messages_display(frm, r.message);
            }
        }
    });
}

function update_messages_display(frm, messages) {
    const container = frm.custom_messages_section.find('.mss-custom-chats-container');
    
    // Group messages by contact
    const contactMessages = {};
    messages.forEach(msg => {
        const contact = msg.type === 'Incoming' ? msg.from : msg.to;
        if (!contactMessages[contact]) {
            contactMessages[contact] = [];
        }
        contactMessages[contact].push(msg);
    });
    
    // Sort contacts alphabetically
    const sortedContacts = Object.keys(contactMessages).sort((a, b) => {
        const nameA = (contactMessages[a][0].contact_name || '').toLowerCase();
        const nameB = (contactMessages[b][0].contact_name || '').toLowerCase();
        if (nameA && nameB) {
            return nameA.localeCompare(nameB);
        }
        // If no contact name, sort by phone number
        return a.localeCompare(b);
    });
    
    // Create or update chat sections for each contact
    sortedContacts.forEach(contact => {
        const msgs = contactMessages[contact];
        // Sort messages by creation time
        msgs.sort((a, b) => new Date(a.creation) - new Date(b.creation));
        
        // Get contact name
        frappe.call({
            method: 'mss_custom.mss_custom.whatsapp.get_contact_name',
            args: {
                phone_number: contact
            },
            callback: function(r) {
                const contactName = r.message || contact;
                
                // Check if chat section already exists
                let chatSection = container.find(`[data-contact="${contact}"]`);
                
                if (chatSection.length === 0) {
                    // Create new chat section if it doesn't exist
                    chatSection = $(`
                        <div class="mss-custom-chat-section" data-contact="${contact}">
                            <div class="mss-custom-contact-header">
                                <h3>${frappe.utils.escape_html(contactName)}</h3>
                                <span class="mss-custom-contact-number">${frappe.utils.escape_html(contact)}</span>
                            </div>
                            <div class="mss-custom-timeline"></div>
                        </div>
                    `);
                    
                    // Find the correct position to insert the new section
                    let inserted = false;
                    container.children().each(function() {
                        const existingName = $(this).find('h3').text().toLowerCase();
                        if (contactName.toLowerCase().localeCompare(existingName) < 0) {
                            $(this).before(chatSection);
                            inserted = true;
                            return false;
                        }
                    });
                    
                    if (!inserted) {
                        container.append(chatSection);
                    }
                }
                
                // Update the timeline with messages
                const timeline = chatSection.find('.mss-custom-timeline');
                const wasAtBottom = isScrolledToBottom(timeline);
                
                timeline.empty(); // Clear existing messages
                
                msgs.forEach(msg => {
                    const msgClass = msg.type === 'Incoming' ? 'mss-custom-message-received' : 'mss-custom-message-sent';
                    const timestamp = frappe.datetime.str_to_user(msg.creation);
                    
                    let messageContent = '';
                    if (msg.content_type === 'text') {
                        messageContent = frappe.utils.escape_html(msg.message || '');
                    } else if (msg.message) {
                        const fileName = msg.message.split('/').pop() || 'File';
                        messageContent = `<a href="${msg.message}" target="_blank">${fileName}</a>`;
                    }
                    
                    const messageElement = $(`
                        <div class="mss-custom-timeline-item">
                            <div class="${msgClass}">
                                <div class="mss-custom-message-content">
                                    ${messageContent}
                                </div>
                                <div class="mss-custom-message-${msg.type === 'Incoming' ? 'received' : 'sent'}-timestamp">${timestamp}</div>
                                ${msg.type !== 'Incoming' && msg.owner ? `<div class="mss-custom-message-owner">${frappe.utils.escape_html(msg.owner)}</div>` : ''}
                            </div>
                        </div>
                    `);
                    
                    timeline.append(messageElement);
                });
                
                // Scroll to bottom if it was at bottom before update
                if (wasAtBottom) {
                    scrollToBottom(timeline);
                }
            }
        });
    });
}

function isScrolledToBottom(element) {
    const threshold = 50; // pixels from bottom to consider "at bottom"
    return element[0].scrollHeight - element.scrollTop() - element.outerHeight() <= threshold;
}

function scrollToBottom(element) {
    element.scrollTop(element[0].scrollHeight);
}

function subscribe_to_updates(frm) {
    // Subscribe to WhatsApp Message updates
    frappe.realtime.on('latest_chat_updates', function(data) {
        // Only update if the message is related to this Issue
        if (data.reference_doctype === "Issue" && data.reference_name === frm.doc.name) {
            // Get all current messages to maintain sorting
            frappe.call({
                method: 'mss_custom.mss_custom.whatsapp.get_whatsapp_messages',
                args: {
                    issue_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        // Update the entire display to maintain alphabetical order
                        update_messages_display(frm, r.message);
                    }
                }
            });
        }
    });
}

function update_contact_timeline(chatSection, messages) {
    const timeline = chatSection.find('.mss-custom-timeline');
    timeline.empty(); // Clear existing messages
    
    // Sort messages by creation time
    messages.sort((a, b) => new Date(a.creation) - new Date(b.creation));
    
    messages.forEach(msg => {
        const msgClass = msg.type === 'Incoming' ? 'mss-custom-message-received' : 'mss-custom-message-sent';
        const timestamp = frappe.datetime.str_to_user(msg.creation);
        
        let messageContent = '';
        if (msg.content_type === 'text') {
            messageContent = frappe.utils.escape_html(msg.message || '');
        } else if (msg.message) {
            const fileName = msg.message.split('/').pop() || 'File';
            messageContent = `<a href="${msg.message}" target="_blank">${fileName}</a>`;
        }
        
        const messageElement = $(`
            <div class="mss-custom-timeline-item">
                <div class="${msgClass}">
                    <div class="mss-custom-message-content">
                        ${messageContent}
                    </div>
                    <div class="mss-custom-message-${msg.type === 'Incoming' ? 'received' : 'sent'}-timestamp">${timestamp}</div>
                    ${msg.type !== 'Incoming' && msg.owner ? `<div class="mss-custom-message-owner">${frappe.utils.escape_html(msg.owner)}</div>` : ''}
                </div>
            </div>
        `);
        
        timeline.append(messageElement);
    });
    
    // Scroll to bottom
    timeline.parent().scrollTop(timeline[0].scrollHeight);
}