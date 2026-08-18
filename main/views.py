from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Case, Value, IntegerField, When
from . import models
from user import models as user_models

# Create your views here.


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
        
        # Update Name & Description
        name = request.POST.get("name")
        description = request.POST.get("description")
        
        if name:
            case.name = name.strip()
            
        if description is not None:
            case.description = description.strip()

        # Update status
        new_status = request.POST.get("status")
        if new_status in ["not_started", "working", "completed"]:
            case.status = new_status

        case.save()

        # Update assigned employees
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