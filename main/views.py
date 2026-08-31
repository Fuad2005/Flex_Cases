from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Case, Value, IntegerField, When
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import models
# from .utils import send_whatsapp_message
from user import models as user_models
from django.conf import settings
import os
import json

# Create your views here.


# @csrf_exempt
# def whatsapp_webhook(request):

#     print("\n========== WHATSAPP WEBHOOK ==========")
#     print("METHOD:", request.method)
#     print("PATH:", request.path)
#     print("BODY:", request.body.decode("utf-8"))
#     print("======================================\n")

#     # 1. VERIFICATION HANDSHAKE (GET)
#     if request.method == 'GET':
#         mode = request.GET.get('hub.mode')
#         token = request.GET.get('hub.verify_token')
#         challenge = request.GET.get('hub.challenge')

#         if mode == 'subscribe' and token == VERIFY_TOKEN:
#             return HttpResponse(challenge, status=200)
#         return HttpResponse('Verification failed', status=403)

#     # 2. INCOMING MESSAGES & AUTOMATED REPLIES (POST)
#     elif request.method == 'POST':
#         try:
#             data = json.loads(request.body.decode('utf-8'))

#             entries = data.get('entry', [])
#             for entry in entries:
#                 changes = entry.get('changes', [])
#                 for change in changes:
#                     value = change.get('value', {})
#                     messages = value.get('messages', [])

#                     if messages:
#                         message = messages[0]
#                         sender_phone = message.get('from')  # Sender's phone number (e.g. 994702148626)
                        
#                         # Check if it's a standard text message
#                         if message.get('type') == 'text':
#                             message_body = message.get('text', {}).get('body', '')

#                             # Log the incoming message to your Django console
#                             print(f"\n[RECEIVED] Message from {sender_phone}: '{message_body}'\n")

#                             # Build your automated reply text
#                             reply_text = f"🤖 Automated Reply: We received your message ('{message_body}')."

#                             # Send the automated reply back via Meta's Graph API
#                             api_response = send_whatsapp_message(sender_phone, reply_text)
#                             print(f"[SENT] API Response: {api_response}\n")

#         except Exception as e:
#             print(f"Webhook processing error: {e}")

#         # Meta requires a fast 200 OK HTTP response
#         return HttpResponse('EVENT_RECEIVED', status=200)



def send_new_case_notification(request, new_case, full_name):
    # Retrieve emails for all active employees
    employee_emails = list(
        user_models.Person.objects.filter(person_type='employee')
        .exclude(email__isnull=True)
        .exclude(email__exact='')
        .values_list('email', flat=True)
    )

    if not employee_emails:
        return

    # Build absolute URL for the case detail button
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    case_url = f"{protocol}://{domain}/case/{new_case.id}/"

    subject = f"🆕 New Case Alert: Case from {full_name}"

    # Plain text fallback
    text_content = f"""
Hello,

A new case from {full_name} has been submitted and is ready to be reviewed.

View details here: {case_url}
"""

    # HTML body with button
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .container {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; padding: 20px; }}
        .header {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #1a1a1a; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            font-size: 14px;
            color: #ffffff !important;
            background-color: #007bff;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">New Case Submitted</div>
        <p>There is a new case from <strong>{full_name}</strong> to be reviewed.</p>
        <p>
            <a href="{case_url}" class="button">View Case Detail</a>
        </p>
    </div>
</body>
</html>
"""

    # Construct and send email (using BCC to protect recipient privacy)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.DEFAULT_FROM_EMAIL],
        bcc=employee_emails
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)

@csrf_exempt
def google_form_webhook(request):
    # Handle health-checks or manual browser checks
    if request.method == 'GET':
        return JsonResponse({'status': 'online', 'message': 'Google Form Webhook endpoint is active.'}, status=200)
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # Extract variables
            user_email = data.get('user_email')
            full_name = data.get('Adınız və soyadınız', 'Unknown')
            phone_number = data.get('Əlaqə nömrəniz', 'N/A')
            location_info = data.get('Layihə və ya problemin baş verdiyi məkan haqqında', 'N/A')
            
            category = data.get('Sorğunuz nə ilə bağlıdır::') or data.get('Sorğunuz nə ilə bağlıdır:', 'N/A')
            description_text = data.get('Problem haqqında qısa məlumat::') or data.get('Problem haqqında qısa məlumat:', 'N/A')
            description_text_html = description_text.replace('\n', '<br>')

            # Format Name and Description
            case_name = f"Case from {full_name}"
            
            case_description = f"""
<p><strong>👤 Name:</strong> {full_name}</p>
<p><strong>📧 Email:</strong> {user_email}</p>
<p><strong>📞 Phone:</strong> {phone_number}</p>
<p><strong>📍 Location/Project:</strong> {location_info}</p>
<p><strong>🏷️ Category:</strong> {category}</p>
<p><strong>📝 Description:</strong> </br>{description_text_html}</p>
            """.strip()

            # Create Case model instance
            new_case = models.Case.objects.create(
                name=case_name,
                description=case_description,
            )

            print(f"\n✅ Case #{new_case.id} successfully created: '{new_case.name}'\n")

            # Trigger email notification to employees
            send_new_case_notification(request, new_case, full_name)


            return JsonResponse({'status': 'success', 'case_id': new_case.id}, status=201)

        except Exception as e:
            print(f"Error saving case: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'method not allowed'}, status=405)




# Dashboard
# =================================================================
@login_required
def dashboard(request):
    person = request.user.person

    all_cases = models.Case.objects.order_by("-created_at")
    working_cases = all_cases.filter(status="working")
    completed_cases = all_cases.filter(status="completed")

    employees = user_models.Person.objects.filter(person_type="employee")


    context = {
        "person": person,
        "all_cases": all_cases,
        "working_cases": working_cases,
        "completed_cases": completed_cases,
        "employees": employees
    }

    return render(request, "main/dashboard.html", context)


# =================================================================



# Case
# =================================================================
@login_required
def create_case(request):
    person = request.user.person

    if person.person_type != "manager":
        return redirect("dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        assigned_to = request.POST.getlist("assigned_to")

        case = models.Case.objects.create(
            name=name,
            description=description
        )

        case.assigned_to.set(assigned_to)

        messages.success(request, 'Case created successfully!', extra_tags='case_created')
        return redirect('dashboard')

    employees = user_models.Person.objects.filter(
        person_type="employee"
    )

    context = {
        "person": person,
        "employees": employees,
    }

    return render(request, "main/create-case.html", context)



@login_required
def all_cases(request):
    person = request.user.person

    cases_qs = models.Case.objects.all()

    # Search filter
    query = request.GET.get('q', '').strip()
    if query:
        cases_qs = cases_qs.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Status filter
    status = request.GET.get('status', '').strip().lower()
    if status in ['not_started', 'working', 'completed']:
        cases_qs = cases_qs.filter(status=status)

    # Assigned employee filter
    assigned_employee_id = request.GET.get('assigned_to', '').strip()
    if assigned_employee_id:
        cases_qs = cases_qs.filter(assigned_to__id=assigned_employee_id)

    # Annotate status with numerical order (1: not_started, 2: working, 3: completed)
    cases_qs = cases_qs.annotate(
        status_order=Case(
            When(status='not_started', then=Value(1)),
            When(status='working', then=Value(2)),
            When(status='completed', then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at').strip()
    
    if sort_by == 'status':
        cases_qs = cases_qs.order_by('status_order')
    elif sort_by == '-status':
        cases_qs = cases_qs.order_by('-status_order')
    elif sort_by in ['name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at']:
        cases_qs = cases_qs.order_by(sort_by)
    else:
        cases_qs = cases_qs.order_by('-created_at')

    # Pagination (10 per page)
    paginator = Paginator(cases_qs.distinct(), 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Stat counters
    all_cases_count = models.Case.objects.count()
    working_cases_count = models.Case.objects.filter(status="working").count()
    completed_cases_count = models.Case.objects.filter(status="completed").count()
    not_started_cases_count = all_cases_count - working_cases_count - completed_cases_count

    employees = user_models.Person.objects.filter(person_type="employee")

    context = {
        "person": person,
        "employees": employees,
        "all_cases": page_obj,
        "page_obj": page_obj,
        "total_cases_count": all_cases_count,
        "working_cases_count": working_cases_count,
        "completed_cases_count": completed_cases_count,
        "not_started_cases_count": not_started_cases_count,
        "selected_status": status,
        "selected_assigned_to": assigned_employee_id,
        "selected_sort": sort_by,
        "search_query": query,
    }

    return render(request, "main/all-cases.html", context)


@login_required
def update_case(request, case_id):
    if request.method == "POST":
        case = get_object_or_404(models.Case, id=case_id)
        person = get_object_or_404(user_models.Person, user=request.user)

        # Employee Logic: Only add the current employee to assigned_to
        if person.person_type == "employee":
            case.assigned_to.add(person)
            if case.status == "not_started":
                case.status = "working"
            case.save()
            messages.success(request, "You have taken this case!")
            return redirect(request.META.get('HTTP_REFERER', 'all-cases'))

        # Manager Logic: Full update
        name = request.POST.get("name")
        description = request.POST.get("description")
        
        if name:
            case.name = name.strip()
            
        if description is not None:
            case.description = description.strip()

        new_status = request.POST.get("status")
        if new_status in ["not_started", "working", "completed"]:
            case.status = new_status

        case.save()

        assigned_to_ids = request.POST.getlist("assigned_to")
        case.assigned_to.set(assigned_to_ids)

        messages.success(request, "Case updated successfully!")
        
    return redirect(request.META.get('HTTP_REFERER', 'all-cases'))

@login_required
def delete_case(request, case_id):
    if request.method == "POST":
        case = get_object_or_404(models.Case, id=case_id)
        case.delete()
        messages.success(request, "Case deleted successfully!")
    return redirect('all-cases')



@login_required
def case_detail(request, case_id):
    person = request.user.person

    case = get_object_or_404(models.Case, id=case_id)

    employees = user_models.Person.objects.filter(
        person_type="employee"
    )

    context = {
        "person": person,
        "employees": employees,
        "case": case
    }

    return render(request, "main/case-detail.html", context)


# =================================================================



# Staff
# =================================================================
@login_required
def staff(request):
    person = request.user.person

    # if person.person_type != "manager":
    #     return redirect("dashboard")

    employees = user_models.Person.objects.filter(person_type="employee")
    managers = user_models.Person.objects.filter(person_type="manager")

    context = {
        "person": person,
        "employees": employees,
        "managers": managers
    }

    return render(request, "main/staff.html", context)




# ================================================================


def privacy(request):
    return render(request, "main/privacy-policy.html")