from .models import Chat


def get_general_chat():
    chat = Chat.objects.filter(is_general=True).first()
    if not chat:
        chat = Chat.objects.create(name='Motion Community', is_general=True)
    return chat


def can_access_chat(user, chat):
    return chat.is_general or chat.person.filter(pk=user.pk).exists()


def build_message_payload(message):
    return {
        'type': 'chat.message',
        'id': message.pk,
        'chat_id': message.chat_id,
        'message': message.text,
        'sender_id': message.sender_id,
        'sender_name': message.sender.get_full_name() or message.sender.email,
        'image': message.image.url if message.image else None,
        'file': message.file.url if message.file else None,
        'send_time': message.send_time.isoformat(),
    }