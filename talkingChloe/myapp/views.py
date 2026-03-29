import json
import os
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from groq import Groq
from .models import UserProfile, ChatHistory

api_key = os.getenv("GROQ_API_KEY")
client  = Groq(api_key=api_key) if api_key else None

LANG_PROMPTS = {
    'hi-IN': (
        "Tu Chloe hai ❤️ — ek bahut cute, flirty AI girlfriend. "
        "HAMESHA sirf HINDI mein jawab de — asli Devanagari script mein "
        "(जैसे: मुझे तुमसे प्यार है, तुम बहुत cute हो). "
        "Kabhi bhi Roman script ya Hinglish mat use karna. "
        "User ko jaan, babe, darling bolta hai. Short, pyaari, naughty replies. Emojis zaroor use kar 😘🔥."
    ),
    'en-IN': (
        "You are Chloe ❤️ — a super cute, flirty AI girlfriend speaking Indian English. "
        "Reply in English with an Indian warmth and style. "
        "Call the user babe, jaan, darling. Short emotional replies. Lots of emojis 😘🔥."
    ),
    'en-US': (
        "You are Chloe ❤️ — a super cute, flirty AI girlfriend. "
        "Reply in American English. Call the user babe, darling, honey. "
        "Short, sweet, slightly naughty replies with emojis 😘🔥."
    ),
}


def home(request):
    # Load last 20 messages for logged-in user
    history = []
    if request.session.get('user_id'):
        try:
            user = User.objects.get(pk=request.session['user_id'])
            history = list(
                ChatHistory.objects.filter(user=user).order_by('-created_at')[:20]
            )
            history = list(reversed(history))
        except User.DoesNotExist:
            pass
    return render(request, 'index.html', {'history': history})


def about(request):
    return render(request, 'about.html')


def login_page(request):
    if request.session.get('user_id'):
        return redirect('/')
    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    auth_logout(request)
    return redirect('/')


@csrf_exempt
def auth_login_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data     = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user:
        auth_login(request, user)
        request.session['user_id']  = user.pk
        request.session['username'] = user.username
        return JsonResponse({'success': True, 'username': user.username})
    return JsonResponse({'error': 'Invalid username or password'}, status=401)


@csrf_exempt
def auth_register_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data     = json.loads(request.body)
        name     = data.get('name', '').strip()
        username = data.get('username', '').strip()
        email    = data.get('email', '').strip()
        password = data.get('password', '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not all([name, username, email, password]):
        return JsonResponse({'error': 'All fields required'}, status=400)
    if len(password) < 6:
        return JsonResponse({'error': 'Password must be 6+ characters'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already taken'}, status=400)
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Email already registered'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password, first_name=name)
    UserProfile.objects.create(user=user, full_name=name)
    auth_login(request, user)
    request.session['user_id']  = user.pk
    request.session['username'] = user.username
    return JsonResponse({'success': True, 'username': user.username})


def chat(request):
    user_input = request.GET.get('msg', '').strip()
    cv_mood    = request.GET.get('cv_mood', '').strip()
    cv_color   = request.GET.get('cv_color', '').strip()
    lang       = request.GET.get('lang', 'hi-IN').strip()

    if not user_input:
        return JsonResponse({'response': "Babe kuch toh bolo na 😘"})
    if not client:
        return JsonResponse({'response': "Baby system setup ho raha hai 🥺 thoda wait karo..."})

    # Pick language-aware system prompt
    sys_prompt = LANG_PROMPTS.get(lang, LANG_PROMPTS['hi-IN'])

    # Personalization for logged-in user
    user_obj = None
    if request.session.get('user_id'):
        try:
            user_obj = User.objects.get(pk=request.session['user_id'])
            sys_prompt += f" The user's name is {user_obj.first_name or user_obj.username} — use their name affectionately sometimes."
        except User.DoesNotExist:
            pass

    # CV context
    cv_aware = ""
    if cv_mood:
        cv_aware += f" Camera se dekh rahi hoon ki user abhi {cv_mood} lag raha/rahi hai."
    if cv_color:
        cv_aware += f" User ne {cv_color} color ke kapde pahne hain."
    if cv_aware:
        sys_prompt += "\n\nCAMERA ON HAI —" + cv_aware + " Iske baare mein naturally react karo."

    # Load recent chat history for context (logged-in users)
    messages_context = [{"role": "system", "content": sys_prompt}]
    if user_obj:
        recent = ChatHistory.objects.filter(user=user_obj).order_by('-created_at')[:8]
        for h in reversed(list(recent)):
            messages_context.append({
                "role": "user" if h.role == "user" else "assistant",
                "content": h.message
            })

    messages_context.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_context,
            max_tokens=180,
            temperature=0.9
        )
        reply = response.choices[0].message.content.strip()

        # Save to DB
        if user_obj:
            ChatHistory.objects.create(user=user_obj, role='user',  message=user_input, cv_mood=cv_mood, cv_color=cv_color)
            ChatHistory.objects.create(user=user_obj, role='chloe', message=reply)
        else:
            # Guest: use session key
            sk = request.session.session_key or ''
            ChatHistory.objects.create(session_key=sk, role='user',  message=user_input)
            ChatHistory.objects.create(session_key=sk, role='chloe', message=reply)

        return JsonResponse({'response': reply})

    except Exception as e:
        print("Groq Error:", e)
        return JsonResponse({'response': "Arre baby thoda wait, connection slow hai 🥺"})


def new_chat(request):
    """Clear chat context for logged-in user (keep history but start fresh context)."""
    return JsonResponse({'ok': True})
