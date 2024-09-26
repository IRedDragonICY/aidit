$(document).ready(function() {
    $('#toggle-sidebar').on('click', function() {
        $('#sidebar-section').toggleClass('collapsed');
    });

    $('#upload-form').on('submit', function(e) {
        e.preventDefault();

        const fileInput = $('#pdfFile')[0];
        if (fileInput.files.length === 0) {
            alert("Silakan pilih file PDF.");
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        $('#loading').show();
        $('#upload-error').addClass('d-none');

        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success(response) {
                $('#loading').hide();
                if (response.status === "success") {
                    $('#upload-section').hide();
                    $('#chat-section').show();
                    const sessionItem = `<li class="nav-item"><a class="nav-link" href="#"><i class="fa fa-folder-open"></i> ${response.session_name}</a></li>`;
                    $('.sidebar .nav').append(sessionItem);
                } else {
                    $('#upload-error').removeClass('d-none').text("Error: " + response.message);
                }
            },
            error(xhr, status, error) {
                $('#loading').hide();
                $('#upload-error').removeClass('d-none').text("Terjadi kesalahan saat memproses file.");
            }
        });
    });

    $('#chat-form').on('submit', function(e) {
        e.preventDefault();

        const userInput = $('#user-input').val().trim();
        if (userInput === "") return;

        appendMessage('user', userInput);
        $('#user-input').val('');
        scrollChatToBottom();

        $.ajax({
            url: '/chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: userInput }),
            success(response) {
                if (response.status === "success") {
                    appendMessage('ai', response.reply);
                    scrollChatToBottom();
                } else {
                    appendMessage('ai', "Maaf, terjadi kesalahan: " + response.message);
                    scrollChatToBottom();
                }
            },
            error(xhr, status, error) {
                appendMessage('ai', "Maaf, terjadi kesalahan saat mengirim pesan.");
                scrollChatToBottom();
            }
        });
    });

    const appendMessage = (sender, message) => {
        const messageClass = sender === 'user' ? 'user' : 'ai';
        const messageElement = `
            <div class="message ${messageClass}">
                <div class="message-content">
                    ${escapeHtml(message)}
                </div>
            </div>
        `;
        $('#chat-box').append(messageElement);
    };

    const scrollChatToBottom = () => {
        const chatBox = $('#chat-box');
        chatBox.scrollTop(chatBox[0].scrollHeight);
    };

    const escapeHtml = (text) => {
        return $('<div>').text(text).html();
    };
});
