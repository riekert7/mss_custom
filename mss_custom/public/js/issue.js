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
                                    <h3>Messages Timeline</h3>
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
        // First try to sort by contact name
        const nameA = frappe.utils.escape_html(contactMessages[a][0].contact_name || a);
        const nameB = frappe.utils.escape_html(contactMessages[b][0].contact_name || b);
        return nameA.localeCompare(nameB);
    });
    
    // Create or update chat sections for each contact in sorted order
    sortedContacts.forEach(contact => {
        const msgs = contactMessages[contact];
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
                    
                    container.append(chatSection);
                }
                
                // Update the timeline with messages
                const timeline = chatSection.find('.mss-custom-timeline');
                timeline.empty(); // Clear existing messages
                
                // Sort messages by creation time
                msgs.sort((a, b) => new Date(a.creation) - new Date(b.creation));
                
                msgs.forEach(msg => {
                    const msgClass = msg.type === 'Incoming' ? 'mss-custom-message-received' : 'mss-custom-message-sent';
                    const timestamp = frappe.datetime.str_to_user(msg.creation);
                    
                    let messageContent = msg.content_type === 'text' 
                        ? frappe.utils.escape_html(msg.message)
                        : `<a href="${msg.message}" target="_blank">${msg.message.split('/').pop()}</a>`;
                    
                    const messageElement = $(`
                        <div class="mss-custom-timeline-item">
                            <div class="${msgClass}">
                                <p>${messageContent}</p>
                                <div class="mss-custom-message-timestamp">${timestamp}</div>
                            </div>
                        </div>
                    `);
                    
                    timeline.append(messageElement);
                });
                
                // Scroll to bottom
                timeline.parent().scrollTop(timeline[0].scrollHeight);
            }
        });
    });
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
        
        let messageContent = msg.content_type === 'text' 
            ? frappe.utils.escape_html(msg.message)
            : `<a href="${msg.message}" target="_blank">${msg.message.split('/').pop()}</a>`;
        
        const messageElement = $(`
            <div class="mss-custom-timeline-item">
                <div class="${msgClass}">
                    <p>${messageContent}</p>
                    <div class="mss-custom-message-timestamp">${timestamp}</div>
                </div>
            </div>
        `);
        
        timeline.append(messageElement);
    });
    
    // Scroll to bottom
    timeline.parent().scrollTop(timeline[0].scrollHeight);
}