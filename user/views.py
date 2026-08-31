from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from .models import Person
from django.contrib.auth.forms import AuthenticationForm


def login_view(request):
    if request.method == "POST":

        form = AuthenticationForm(request, data=request.POST)

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        # Add the authentication error to the form
        form.add_error(
            None,
            "Invalid username or password."
        )

        return render(
            request,
            "user/login.html",
            {
                "form": form
            }
        )

    form = AuthenticationForm()

    return render(
        request,
        "user/login.html",
        {
            "form": form
        }
    )


@login_required
def add_employee(request):
    # Ensure only managers can access this view
    if request.user.person.person_type != Person.PersonType.MANAGER:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        # person_type = request.POST.get("person_type", Person.PersonType.EMPLOYEE)
        person_type = Person.PersonType.EMPLOYEE

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose a different one.")
            return render(request, "user/add_employee.html")

        try:
            with transaction.atomic():
                # 1. Create Django User
                user = User.objects.create_user(
                    username=username,
                    password=password,
                )

                # 2. Create One-to-One Person Model
                Person.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    person_type=person_type,
                    email=email
                )

            messages.success(request, f"User {username} added successfully!", extra_tags="employee_created")
            return redirect("staff")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    person = request.user.person
    context = {
        "person": person
    }
    return render(request, "user/add-employee.html", context)