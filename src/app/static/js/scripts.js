// scripts.js
$(document).ready(function() {
    $('#toggle-sidebar').on('click', function() {
        $('#sidebar-section').toggleClass('collapsed');
    });

    let chatSocket = null;
    let isProcessing = false;

    function initializeWebSocket() {
        chatSocket = new WebSocket('ws://localhost:1010/ws/chat');

        chatSocket.onopen = function() {
            // Connection established, waiting for initial greeting
        };

        chatSocket.onmessage = function(event) {
            if (event.data.startsWith('{')) {
                const data = JSON.parse(event.data);
                if (data.status === 'completed') {
                    isProcessing = false;
                    if ($('#chat-box .message.ai').length === 1) {
                        showFileUploadForm();
                    }
                } else if (data.status === 'file_processed') {
                    isProcessing = false;
                    $('#loading').hide();
                    $('#progress-area').hide();
                    appendMessage('ai', "File berhasil diproses dan dianalisis.");
                    // Remove the file upload form
                    $('#upload-form').closest('.message.ai').remove();
                } else if (data.error) {
                    isProcessing = false;
                    $('#loading').hide();
                    $('#progress-area').hide();
                    appendMessage('ai', "Maaf, terjadi kesalahan: " + data.error);
                    scrollChatToBottom();
                } else if (data.status === 'reset_completed') {
                    $('#chat-box').empty();
                    appendMessage('ai', "Percakapan telah direset.");
                } else if (data.status === 'message_deleted') {
                }
            } else {
                if (isProcessing && $('#progress-area').is(':visible')) {
                    $('#progress-text').append(event.data);
                } else {
                    appendToLastMessage('ai', event.data);
                }
                scrollChatToBottom();
            }
        };

        chatSocket.onerror = function(error) {
            appendMessage('ai', "Maaf, terjadi kesalahan.");
            scrollChatToBottom();
        };

        chatSocket.onclose = function() {
            console.log("Chat WebSocket closed");
        };
    }

    initializeWebSocket();

    function showFileUploadForm() {
        const fileUploadForm = `
            <div class="message ai">
                <div class="message-content">
                    <form id="upload-form">
                        <div class="mb-3">
                            <label for="pdfFile" class="form-label"><i class="fa fa-file-pdf text-danger"></i> Silakan unggah file PDF Anda:</label>
                            <input type="file" class="form-control" id="pdfFile" name="pdfFile" accept="application/pdf" required>
                        </div>
                        <button type="submit" class="btn btn-primary"><i class="fa fa-upload"></i> Unggah dan Proses</button>
                    </form>
                    <div id="loading" class="text-center mt-4" style="display: none;">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Memproses...</span>
                        </div>
                        <p class="mt-2">File Anda sedang diproses, harap tunggu...</p>
                    </div>
                    <div id="upload-error" class="alert alert-danger mt-3 d-none" role="alert">
                        Terjadi kesalahan saat memproses file.
                    </div>
                </div>
            </div>
        `;
        $('#chat-box').append(fileUploadForm);
        scrollChatToBottom();

        $('#upload-form').on('submit', function(e) {
            e.preventDefault();

            if (isProcessing) {
                alert("Proses sedang berjalan, harap tunggu.");
                return;
            }

            const fileInput = $('#pdfFile')[0];
            if (fileInput.files.length === 0) {
                alert("Silakan pilih file PDF.");
                return;
            }

            const file = fileInput.files[0];
            const reader = new FileReader();
            reader.onload = function(event) {
                const arrayBuffer = event.target.result;
                const uint8Array = new Uint8Array(arrayBuffer);

                $('#loading').show();
                $('#upload-error').addClass('d-none');
                isProcessing = true;

                chatSocket.send(JSON.stringify({
                    command: 'upload_file',
                    pdf_bytes: Array.from(uint8Array)
                }));

                $('#progress-area').show();
                $('#progress-text').text('Memulai ekstraksi data...');
            };
            reader.readAsArrayBuffer(file);
        });
    }

    $('#chat-form').on('submit', function(e) {
        e.preventDefault();

        if (isProcessing) {
            alert("Proses sedang berjalan, harap tunggu.");
            return;
        }

        const userInput = $('#user-input').val().trim();
        if (userInput === "") return;

        appendMessage('user', userInput);
        $('#user-input').val('');
        scrollChatToBottom();

        isProcessing = true;

        chatSocket.send(JSON.stringify({
            command: 'user_message',
            message: userInput
        }));
    });

    $('#stop-button').on('click', function() {
        if (isProcessing) {
            chatSocket.send(JSON.stringify({ command: 'stop' }));
            isProcessing = false;
            $('#progress-area').hide();
        }
    });

    $('#new-chat-btn').on('click', function() {
        chatSocket.send(JSON.stringify({ command: 'reset' }));
    });

    $(document).on('click', '.delete-button', function() {
        const messageElement = $(this).closest('.message');
        const index = messageElement.index();
        chatSocket.send(JSON.stringify({ command: 'delete_message', message_index: index }));
        messageElement.remove();
    });

    const appendMessage = (sender, message) => {
        const messageClass = sender === 'user' ? 'user' : 'ai';
        const messageElement = `
            <div class="message ${messageClass}">
                <div class="message-content">
                    ${escapeHtml(message)}
                </div>
                <div class="message-actions">
                    <button class="btn btn-sm btn-secondary delete-button"><i class="fa fa-trash"></i></button>
                    ${sender === 'ai' ? '<button class="btn btn-sm btn-secondary regenerate-button"><i class="fa fa-sync"></i></button>' : ''}
                </div>
            </div>
        `;
        $('#chat-box').append(messageElement);
    };

    const appendToLastMessage = (sender, message) => {
        const messageClass = sender === 'user' ? 'user' : 'ai';
        const lastMessage = $('#chat-box .message').last();
        if (lastMessage.length && lastMessage.hasClass(messageClass)) {
            const contentDiv = lastMessage.find('.message-content');
            contentDiv.html(contentDiv.html() + escapeHtml(message));
        } else {
            appendMessage(sender, message);
        }
    };

    const scrollChatToBottom = () => {
        const chatBox = $('#chat-box');
        chatBox.scrollTop(chatBox[0].scrollHeight);
    };

    const escapeHtml = (text) => {
        return $('<div>').text(text).html();
    };

    $(document).on('click', '.regenerate-button', function() {
        if (isProcessing) {
            alert("Proses sedang berjalan, harap tunggu.");
            return;
        }
        isProcessing = true;
        chatSocket.send(JSON.stringify({ command: 'regenerate' }));
    });
});
