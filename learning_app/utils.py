from django.utils import timezone
from .models import ClickstreamEvent
import re
from collections import Counter
import base64
import io

# Import wordcloud library
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Extract user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def get_referrer(request):
    """Extract referrer from request"""
    return request.META.get('HTTP_REFERER', '')


def log_clickstream_event(request, event_name, component, description, user=None):
    """
    Log a clickstream event to the database
    
    Args:
        request: Django HttpRequest object
        event_name: Type of event (from ClickstreamEvent.EVENT_TYPES)
        component: Component where event occurred
        description: Detailed description of the event
        user: User object (optional, will use request.user if not provided)
    """
    # Use provided user or request.user, but allow for anonymous users
    event_user = user if user else (request.user if request.user.is_authenticated else None)
    
    # Create the clickstream event
    ClickstreamEvent.objects.create(
        user=event_user,
        event_context="Learning Platform - ET617 Assignment",
        component=component,
        event_name=event_name,
        description=description,
        origin="web",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        url=request.build_absolute_uri(),
        referrer=get_referrer(request),
        session_id=request.session.session_key or '',
    )


# ============ WORD CLOUD UTILITIES ============

def get_stop_words():
    """Get list of common English stop words to filter out"""
    return {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 'its',
        'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with', 'would', 'you', 'your', 'this', 'these',
        'they', 'them', 'their', 'then', 'than', 'but', 'or', 'so', 'if', 'when', 'where', 'why',
        'how', 'what', 'who', 'which', 'can', 'could', 'should', 'would', 'may', 'might', 'must', 'shall',
        'have', 'had', 'has', 'do', 'does', 'did', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'get', 'got', 'go', 'goes', 'went', 'come', 'came', 'see', 'saw', 'know', 'knew', 'think', 'thought',
        'take', 'took', 'make', 'made', 'give', 'gave', 'say', 'said', 'tell', 'told', 'want', 'wanted',
        'need', 'needed', 'use', 'used', 'work', 'worked', 'call', 'called', 'try', 'tried', 'ask', 'asked',
        'feel', 'felt', 'leave', 'left', 'put', 'turn', 'turned', 'move', 'moved', 'live', 'lived', 'bring',
        'brought', 'happen', 'happened', 'write', 'wrote', 'provide', 'provided', 'sit', 'sat', 'stand',
        'stood', 'lose', 'lost', 'pay', 'paid', 'meet', 'met', 'include', 'included', 'continue', 'continued',
        'set', 'run', 'ran', 'play', 'played', 'turn', 'turned', 'start', 'started', 'show', 'showed',
        'hear', 'heard', 'let', 'help', 'helped', 'keep', 'kept', 'begin', 'began', 'seem', 'seemed',
        'talk', 'talked', 'turn', 'turned', 'start', 'started', 'might', 'could', 'should', 'would'
    }


def process_text_for_word_cloud(text):
    """
    Process text for word cloud generation
    
    Args:
        text (str): Input text to process
        
    Returns:
        list: List of cleaned words ready for frequency counting
    """
    if not text or not isinstance(text, str):
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and special characters, keep only letters and spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Split into words and filter
    words = text.split()
    
    # Get stop words
    stop_words = get_stop_words()
    
    # Filter words
    filtered_words = []
    for word in words:
        # Remove words shorter than 2 characters
        if len(word) < 2:
            continue
        
        # Remove stop words
        if word in stop_words:
            continue
        
        # Remove words that are only numbers
        if word.isdigit():
            continue
        
        filtered_words.append(word)
    
    return filtered_words


def generate_word_cloud_data(text_responses):
    """
    Generate word cloud data from text responses
    
    Args:
        text_responses (list): List of text response strings
        
    Returns:
        dict: Word frequencies dictionary
    """
    if not text_responses:
        return {}
    
    all_words = []
    
    # Process all text responses
    for response in text_responses:
        if response and isinstance(response, str):
            words = process_text_for_word_cloud(response)
            all_words.extend(words)
    
    # Count word frequencies
    word_counts = Counter(all_words)
    
    # Convert to dictionary and limit to top 50 words
    word_cloud_data = dict(word_counts.most_common(50))
    
    return word_cloud_data


def create_word_cloud_visualization(word_cloud_data, max_words=30):
    """
    Create word cloud visualization data for frontend with Mentimeter-style presentation
    
    Args:
        word_cloud_data (dict): Word frequencies dictionary
        max_words (int): Maximum number of words to include
        
    Returns:
        dict: Formatted data for frontend visualization
    """
    if not word_cloud_data:
        return {
            'words': [],
            'total_words': 0,
            'unique_words': 0
        }
    
    # Sort words by frequency and limit
    sorted_words = sorted(word_cloud_data.items(), key=lambda x: x[1], reverse=True)[:max_words]
    
    # Calculate total word count
    total_words = sum(word_cloud_data.values())
    unique_words = len(word_cloud_data)
    
    # Enhanced formatting for Mentimeter-style presentation
    if sorted_words:
        max_freq = sorted_words[0][1]
        min_freq = sorted_words[-1][1]
        
        # Enhanced size range for better visual impact (Mentimeter-style: 16-72px)
        min_size = 16
        max_size = 72
        size_range = max_size - min_size
        
        # Avoid division by zero
        if max_freq == min_freq:
            size_range = 0
        
        formatted_words = []
        for i, (word, freq) in enumerate(sorted_words):
            if max_freq == min_freq:
                size = max_size
            else:
                # Enhanced normalization with power curve for better visual distribution
                normalized = (freq - min_freq) / (max_freq - min_freq)
                # Apply power curve for more dramatic size differences
                size = min_size + (normalized ** 0.7 * size_range)
            
            # Calculate prominence score (0-100) for additional styling
            prominence = round((freq / max_freq) * 100) if max_freq > 0 else 0
            
            # Assign visual weight category
            if prominence >= 80:
                weight = 'heavy'
            elif prominence >= 50:
                weight = 'bold'
            elif prominence >= 25:
                weight = 'medium'
            else:
                weight = 'light'
            
            formatted_words.append({
                'text': word,
                'size': round(size),
                'frequency': freq,
                'percentage': round((freq / total_words) * 100, 1),
                'prominence': prominence,
                'weight': weight,
                'rank': i + 1
            })
    else:
        formatted_words = []
    
    return {
        'words': formatted_words,
        'total_words': total_words,
        'unique_words': unique_words,
        'max_frequency': max_freq if sorted_words else 0
    }


def generate_word_cloud_image(word_cloud_data):
    """
    Generate an actual word cloud image from word frequencies
    
    Args:
        word_cloud_data (dict): Word frequencies dictionary
        
    Returns:
        str: Base64 encoded image data or None if failed
    """
    if not WORDCLOUD_AVAILABLE or not word_cloud_data:
        return None
    
    try:
        # Create word cloud
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white',
            colormap='viridis',
            relative_scaling=0.5,
            max_words=100,
            min_font_size=10,
            max_font_size=70
        ).generate_from_frequencies(word_cloud_data)
        
        # Create plot
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        
        # Save to bytes
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)
        
        # Convert to base64
        image_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Close plot to free memory
        plt.close()
        
        return image_data
    except Exception as e:
        print(f"Error generating word cloud image: {e}")
        return None