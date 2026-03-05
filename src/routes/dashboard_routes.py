from flask import Blueprint, render_template

dashboard = Blueprint("dashboard", __name__)


# Main dashboard landing page
@dashboard.route("/dashboard")
def show_dashboard():
    return render_template("analytics.html")   # new modern UI


# Simple moderation page (optional)
@dashboard.route("/manual_review")
def manual_review():
    return render_template("dashboard.html")   # your old dashboard (fallback)