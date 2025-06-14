TRANSLATIONS = {
    'en': {
        'greeting': 'Hello, this is Delhi Public School reception. How may I help you?',
        'appointment_success': 'Your appointment has been scheduled successfully.',
        'appointment_failed': 'I apologize, but I could not schedule your appointment.',
        'event_registration_success': 'You have been successfully registered for the event.',
        'event_registration_failed': 'I apologize, but the event is full or registration failed.',
        'language_switch': 'I will now switch to {language}.',
        'goodbye': 'Thank you for calling Delhi Public School. Have a great day!',
        'transferring': 'I will transfer your call to {department}.',
        'hold': 'Please hold while I process your request.',
        'appointment_reminder': 'This is a reminder for your appointment with {teacher} on {date} at {time}.',
        'appointment_conflict': 'The requested time is not available. Here are some alternative times: {suggestions}',
        'appointment_conflict_no_suggestions': 'The requested time is not available and no alternatives were found.',
    },
    'hi': {
        'greeting': 'नमस्ते, यह दिल्ली पब्लिक स्कूल रिसेप्शन है। मैं आपकी कैसे सहायता कर सकता/सकती हूं?',
        'appointment_success': 'आपकी मुलाकात सफलतापूर्वक निर्धारित कर दी गई है।',
        'appointment_failed': 'मुझे खेद है, लेकिन मैं आपकी मुलाकात निर्धारित नहीं कर पाया/पाई।',
        'language_switch': 'मैं अब {language} में बदल रहा/रही हूं।',
        'goodbye': 'दिल्ली पब्लिक स्कूल को कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!',
        'transferring': 'मैं आपका कॉल {department} को ट्रांसफर कर रहा/रही हूं।',
        'hold': 'कृपया प्रतीक्षा करें जब तक मैं आपके अनुरोध को संसाधित करता/करती हूं।',
        'appointment_reminder': 'यह {date} को {time} बजे {teacher} के साथ आपकी मुलाकात की याद दिलाने के लिए है।',
        'appointment_conflict': 'अनुरोधित समय उपलब्ध नहीं है। यहाँ कुछ वैकल्पिक समय हैं: {suggestions}',
        'appointment_conflict_no_suggestions': 'अनुरोधित समय उपलब्ध नहीं है और कोई विकल्प नहीं मिला।',
    }
}

def get_translation(key, language='en', **kwargs):
    """Get translation for a key in the specified language with optional formatting."""
    if language not in TRANSLATIONS:
        language = 'en'
    
    translation = TRANSLATIONS[language].get(key, TRANSLATIONS['en'].get(key, key))
    
    if kwargs:
        try:
            return translation.format(**kwargs)
        except KeyError:
            return translation
    
    return translation 