from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from . import models
from user import models as user_models

# Create your views here.



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




@login_required
def create_case(request):
    person = request.user.person

    employees = user_models.Person.objects.filter(
        person_type="employee"
    )

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        assigned_to = request.POST.getlist("assigned_to")

        case = models.Case.objects.create(
            name=name,
            description=description,
        )

        if assigned_to:
            case.assigned_to.set(assigned_to)

        return redirect("dashboard")

    context = {
        "person": person,
        "employees": employees,
    }

    return render(
        request,
        "main/create-case.html",
        context
    )