# from typing import Any
# from django.urls import reverse_lazy
# from django.views.generic import (
#     CreateView,
#     DetailView,
#     ListView,
#     TemplateView,
#     UpdateView,
#     View,
# )
# from root.utils import DeleteMixin
# from user.models import Customer, User
# from user.permission import IsAdminMixin, IsAdminOrAccountingMixin

# from .forms import OrganizationForm, StaticPageForm
# from .models import Organization, StaticPage 
# from django.shortcuts import render, get_object_or_404
# from django.contrib.auth.mixins import LoginRequiredMixin

# class IndexView(LoginRequiredMixin, TemplateView):
#     login_url = '/login/'
#     template_name = "index.html"


# class OrganizationMixin(IsAdminMixin):
#     model = Organization
#     form_class = OrganizationForm
#     paginate_by = 50
#     queryset = Organization.objects.filter(status=True, is_deleted=False)
#     success_url = reverse_lazy("org:organization_detail")


# class OrganizationDetail(DetailView):
#     template_name = "organization/organization_detail.html"

#     def get_object(self):
#         return Organization.objects.last()

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         users = User.objects.all()
#         branches = Branch.objects.filter(
#             is_deleted=False, organization=self.get_object().id
#         )
#         customers = Customer.objects.filter(is_deleted=False)
#         context["branches"] = branches
#         context["customers"] = customers
#         context["users"] = users

#         return context


# class OrganizationCreate(OrganizationMixin, CreateView):
#     template_name = "create.html"


# class OrganizationUpdate(OrganizationMixin, UpdateView):
#     template_name = "update.html"

#     def get_object(self):
#         return Organization.objects.last()


# class OrganizationDelete(OrganizationMixin, DeleteMixin, View):
#     pass


# class StaticPageMixin(IsAdminMixin):
#     model = StaticPage
#     form_class = StaticPageForm
#     paginate_by = 50
#     queryset = StaticPage.objects.filter(status=True, is_deleted=False)
#     success_url = reverse_lazy("org:staticpage_list")
#     search_lookup_fields = ["name", "content", "slug", "keywords"]


# class StaticPageList(StaticPageMixin, ListView):
#     template_name = "staticpage/staticpage_list.html"
#     queryset = StaticPage.objects.filter(status=True, is_deleted=False)


# class StaticPageDetail(StaticPageMixin, DetailView):
#     template_name = "staticpage/staticpage_detail.html"


# class StaticPageCreate(StaticPageMixin, CreateView):
#     template_name = "create.html"


# class StaticPageUpdate(StaticPageMixin, UpdateView):
#     template_name = "update.html"


# class StaticPageDelete(StaticPageMixin, DeleteMixin, View):
#     pass


# from django.db import transaction
# from django.http import HttpRequest, HttpResponse, JsonResponse
# from django.urls import reverse_lazy
# from django.views.generic import (
#     CreateView,
#     DetailView,
#     ListView,
#     TemplateView,
#     UpdateView,
#     View,
# )
# from root.utils import DeleteMixin
# from .models import Branch
# from .forms import BranchForm


# class BranchMixin(IsAdminMixin):
#     model = Branch
#     form_class = BranchForm
#     paginate_by = 50
#     queryset = Branch.objects.filter(status=True, is_deleted=False)
#     success_url = reverse_lazy("org:branch_list")
#     search_lookup_fields = ["name", "address", "contact_number", "branch_manager"]


# class BranchList(BranchMixin, ListView):
#     template_name = "branch/branch_list.html"
#     queryset = Branch.objects.filter(status=True, is_deleted=False)


# class BranchDetail(BranchMixin, DetailView):
#     template_name = "branch/branch_detail.html"


# class BranchCreate(BranchMixin, CreateView):
#     template_name = "create.html"

#     def form_valid(self, form):
#         form.instance.organization = self.request.user.organization
#         return super().form_valid(form)


# class BranchUpdate(BranchMixin, UpdateView):
#     template_name = "update.html"


# class BranchDelete(BranchMixin, DeleteMixin, View):
#     pass


# from .models import Terminal
# from .forms import TerminalForm
# from accounting.models import AccountLedger, AccountSubLedger

# class TerminalMixin:
#     model = Terminal
#     form_class = TerminalForm
#     paginate_by = 10
#     queryset = Terminal.objects.filter(status=True,is_deleted=False)
#     success_url = reverse_lazy('org:terminal_list')

# class TerminalList(TerminalMixin, ListView):
#     template_name = "terminal/terminal_list.html"
#     queryset = Terminal.objects.filter(status=True,is_deleted=False)

# class TerminalDetail(TerminalMixin, DetailView):
#     pass
#     # template_name = "terminal/terminal_detail.html"

# class TerminalCreate(TerminalMixin, CreateView):
#     template_name = "create.html"

#     def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
#         cash_in_hand = AccountLedger.objects.get(ledger_name__iexact="cash-in-hand")
#         card_transactions = AccountLedger.objects.get(ledger_name__iexact="card transactions")
#         mobile_palyemnts = AccountLedger.objects.get(ledger_name__iexact="mobile payments")
#         sales = AccountLedger.objects.get(ledger_name__iexact="sales")

#         branch_code = get_object_or_404(Branch, pk=int(request.POST.get('branch'))).branch_code
#         terminal_no = request.POST.get('terminal_no')

#         ledgers = [cash_in_hand, card_transactions, mobile_palyemnts, sales]

#         for led in ledgers:
#             AccountSubLedger.objects.create(sub_ledger_name=f'{led.ledger_name} {branch_code}-{terminal_no}', ledger=led, is_editable=False)

#         return super().post(request, *args, **kwargs)

# class TerminalUpdate(TerminalMixin, UpdateView):
#     template_name = "update.html"

# class TerminalDelete(TerminalMixin, DeleteMixin, View):
#     pass


# from .models import Table
# from .forms import TableForm
# class TableMixin:
#     model = Table
#     form_class = TableForm
#     paginate_by = 10
#     queryset = Table.objects.filter(status=True,is_deleted=False)
#     success_url = reverse_lazy('org:table_list')

# class TableList(TableMixin, ListView):
#     template_name = "table/table_list.html"
#     queryset = Table.objects.filter(status=True,is_deleted=False)

# class TableDetail(TableMixin, DetailView):
#     template_name = "table/table_detail.html"

# class TableCreate(TableMixin, CreateView):
#     template_name = "create.html"

# class TableUpdate(TableMixin, UpdateView):
#     template_name = "update.html"

# class TableDelete(TableMixin, DeleteMixin, View):
#     pass


# from .models import PrinterSetting
# from .forms import PrinterSettingForm
# class PrinterSettingMixin:
#     model = PrinterSetting
#     form_class = PrinterSettingForm
#     paginate_by = 10
#     queryset = PrinterSetting.objects.filter(status=True,is_deleted=False)
#     success_url = reverse_lazy('org:printersetting_list')

# class PrinterSettingList(PrinterSettingMixin, ListView):
#     template_name = "printersetting/printersetting_list.html"
#     queryset = PrinterSetting.objects.filter(status=True,is_deleted=False)

# class PrinterSettingDetail(PrinterSettingMixin, DetailView):
#     template_name = "printersetting/printersetting_detail.html"

# class PrinterSettingCreate(PrinterSettingMixin, CreateView):
#     template_name = "create.html"

# class PrinterSettingUpdate(PrinterSettingMixin, UpdateView):
#     template_name = "update.html"

# class PrinterSettingDelete(PrinterSettingMixin, DeleteMixin, View):
#     pass

# from .models import MailRecipient, EndDayDailyReport
# from .forms import MailRecipientForm
# class MailRecipientMixin:
#     model = MailRecipient
#     form_class = MailRecipientForm
#     paginate_by = 10
#     queryset = MailRecipient.objects.filter(status=True)
#     success_url = reverse_lazy('org:mailrecipient_list')

# class MailRecipientList(MailRecipientMixin, ListView):
#     template_name = "mailrecipient/mailrecipient_list.html"
#     queryset = MailRecipient.objects.filter(status=True)

# class MailRecipientDetail(MailRecipientMixin, DetailView):
#     template_name = "mailrecipient/mailrecipient_detail.html"

# class MailRecipientCreate(MailRecipientMixin, CreateView):
#     template_name = "create.html"

# class MailRecipientUpdate(MailRecipientMixin, UpdateView):
#     template_name = "update.html"

# class MailRecipientDelete(MailRecipientMixin, DeleteMixin, View):
#     pass


# class EndDayReportList(ListView):
#     paginate_by = 5
#     def get(self, request):
#         reports = EndDayDailyReport.objects.all().order_by('-created_at')
#         return render(request, 'organization/end_day_report_list.html', {'object_list': reports})
        
# from .models import CashDrop
# class DailyEndDayReportList(ListView):
#     paginate_by = 5
#     def get(self, request):
#         reports = CashDrop.objects.all().order_by('-datetime')
#         return render(request, 'organization/daily_sales_report.html', {'object_list': reports})
        
# from .models import CashDrop

# class CashDropMixin(IsAdminOrAccountingMixin):
#     model = CashDrop

#     paginate_by = 5
#     queryset = CashDrop.objects.all().order_by('-datetime')

    

# class DailyEndDayReportList(CashDropMixin, ListView):
#     template_name = "organization/daily_sales_report.html"

from typing import Any
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from root.utils import DeleteMixin
from user.models import Customer, User
from user.permission import IsAdminMixin, IsAdminOrAccountingMixin

from .forms import OrganizationForm, StaticPageForm
from .models import Organization, StaticPage 
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

class IndexView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    template_name = "index.html"


class OrganizationMixin(IsAdminMixin):
    model = Organization
    form_class = OrganizationForm
    paginate_by = 50
    queryset = Organization.objects.filter(status=True, is_deleted=False)
    success_url = reverse_lazy("org:organization_detail")


class OrganizationDetail(DetailView):
    template_name = "organization/organization_detail.html"

    def get_object(self):
        return Organization.objects.last()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.all()
        branches = Branch.objects.filter(
            is_deleted=False, organization=self.get_object().id
        )
        customers = Customer.objects.filter(is_deleted=False)
        context["branches"] = branches
        context["customers"] = customers
        context["users"] = users

        return context


class OrganizationCreate(OrganizationMixin, CreateView):
    template_name = "create.html"


class OrganizationUpdate(OrganizationMixin, UpdateView):
    template_name = "update.html"

    def get_object(self):
        return Organization.objects.last()


class OrganizationDelete(OrganizationMixin, DeleteMixin, View):
    pass


class StaticPageMixin(IsAdminMixin):
    model = StaticPage
    form_class = StaticPageForm
    paginate_by = 50
    queryset = StaticPage.objects.filter(status=True, is_deleted=False)
    success_url = reverse_lazy("org:staticpage_list")
    search_lookup_fields = ["name", "content", "slug", "keywords"]


class StaticPageList(StaticPageMixin, ListView):
    template_name = "staticpage/staticpage_list.html"
    queryset = StaticPage.objects.filter(status=True, is_deleted=False)


class StaticPageDetail(StaticPageMixin, DetailView):
    template_name = "staticpage/staticpage_detail.html"


class StaticPageCreate(StaticPageMixin, CreateView):
    template_name = "create.html"


class StaticPageUpdate(StaticPageMixin, UpdateView):
    template_name = "update.html"


class StaticPageDelete(StaticPageMixin, DeleteMixin, View):
    pass


from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from root.utils import DeleteMixin
from .models import Branch
from .forms import BranchForm


class BranchMixin(IsAdminMixin):
    model = Branch
    form_class = BranchForm
    paginate_by = 50
    queryset = Branch.objects.filter(status=True, is_deleted=False)
    success_url = reverse_lazy("org:branch_list")
    search_lookup_fields = ["name", "address", "contact_number", "branch_manager"]


class BranchList(BranchMixin, ListView):
    template_name = "branch/branch_list.html"
    queryset = Branch.objects.filter(status=True, is_deleted=False)


class BranchDetail(BranchMixin, DetailView):
    template_name = "branch/branch_detail.html"


class BranchCreate(BranchMixin, CreateView):
    template_name = "create.html"

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)


class BranchUpdate(BranchMixin, UpdateView):
    template_name = "update.html"


class BranchDelete(BranchMixin, DeleteMixin, View):
    pass


from .models import Terminal
from .forms import TerminalForm
from accounting.models import AccountLedger, AccountSubLedger

class TerminalMixin:
    model = Terminal
    form_class = TerminalForm
    paginate_by = 10
    queryset = Terminal.objects.filter(status=True,is_deleted=False)
    success_url = reverse_lazy('org:terminal_list')

class TerminalList(TerminalMixin, ListView):
    template_name = "terminal/terminal_list.html"
    queryset = Terminal.objects.filter(status=True,is_deleted=False)

class TerminalDetail(TerminalMixin, DetailView):
    pass
    # template_name = "terminal/terminal_detail.html"

class TerminalCreate(TerminalMixin, CreateView):
    template_name = "create.html"

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        cash_in_hand = AccountLedger.objects.get(ledger_name__iexact="cash-in-hand")
        card_transactions = AccountLedger.objects.get(ledger_name__iexact="card transactions")
        mobile_palyemnts = AccountLedger.objects.get(ledger_name__iexact="mobile payments")
        sales = AccountLedger.objects.get(ledger_name__iexact="sales")

        branch_code = get_object_or_404(Branch, pk=int(request.POST.get('branch'))).branch_code
        terminal_no = request.POST.get('terminal_no')

        ledgers = [cash_in_hand, card_transactions, mobile_palyemnts, sales]

        for led in ledgers:
            AccountSubLedger.objects.create(sub_ledger_name=f'{led.ledger_name} {branch_code}-{terminal_no}', ledger=led, is_editable=False)

        return super().post(request, *args, **kwargs)

class TerminalUpdate(TerminalMixin, UpdateView):
    template_name = "update.html"

class TerminalDelete(TerminalMixin, DeleteMixin, View):
    pass


from .models import Table
from .forms import TableForm
class TableMixin:
    model = Table
    form_class = TableForm
    paginate_by = 10
    queryset = Table.objects.filter(status=True,is_deleted=False)
    success_url = reverse_lazy('org:table_list')

class TableList(TableMixin, ListView):
    template_name = "table/table_list.html"
    queryset = Table.objects.filter(status=True,is_deleted=False)

class TableDetail(TableMixin, DetailView):
    template_name = "table/table_detail.html"

class TableCreate(TableMixin, CreateView):
    template_name = "create.html"

class TableUpdate(TableMixin, UpdateView):
    template_name = "update.html"

class TableDelete(TableMixin, DeleteMixin, View):
    pass


from .models import PrinterSetting
from .forms import PrinterSettingForm
class PrinterSettingMixin:
    model = PrinterSetting
    form_class = PrinterSettingForm
    paginate_by = 10
    queryset = PrinterSetting.objects.filter(status=True,is_deleted=False)
    success_url = reverse_lazy('org:printersetting_list')

class PrinterSettingList(PrinterSettingMixin, ListView):
    template_name = "printersetting/printersetting_list.html"
    queryset = PrinterSetting.objects.filter(status=True,is_deleted=False)

class PrinterSettingDetail(PrinterSettingMixin, DetailView):
    template_name = "printersetting/printersetting_detail.html"

class PrinterSettingCreate(PrinterSettingMixin, CreateView):
    template_name = "create.html"

class PrinterSettingUpdate(PrinterSettingMixin, UpdateView):
    template_name = "update.html"

class PrinterSettingDelete(PrinterSettingMixin, DeleteMixin, View):
    pass

from .models import MailRecipient, EndDayDailyReport
from .forms import MailRecipientForm
class MailRecipientMixin:
    model = MailRecipient
    form_class = MailRecipientForm
    paginate_by = 10
    queryset = MailRecipient.objects.filter(status=True)
    success_url = reverse_lazy('org:mailrecipient_list')

class MailRecipientList(MailRecipientMixin, ListView):
    template_name = "mailrecipient/mailrecipient_list.html"
    queryset = MailRecipient.objects.filter(status=True)

class MailRecipientDetail(MailRecipientMixin, DetailView):
    template_name = "mailrecipient/mailrecipient_detail.html"

class MailRecipientCreate(MailRecipientMixin, CreateView):
    template_name = "create.html"

class MailRecipientUpdate(MailRecipientMixin, UpdateView):
    template_name = "update.html"

class MailRecipientDelete(MailRecipientMixin, DeleteMixin, View):
    pass


class EndDayReportList(ListView):
    paginate_by = 5
    def get(self, request):
        reports = EndDayDailyReport.objects.all().order_by('-created_at')
        return render(request, 'organization/end_day_report_list.html', {'object_list': reports})
    
from .models import CashDrop

from datetime import datetime
class CashDropMixin(IsAdminOrAccountingMixin):
    today_date = datetime.today().date()
    today_date_str = today_date.strftime("%Y-%m-%d")
    model = CashDrop
    paginate_by = 10
    # queryset = CashDrop.objects.all().order_by('-datetime')
    queryset = CashDrop.objects.filter(datetime__startswith=today_date_str).order_by('-datetime')


from datetime import datetime
class DailyEndDayReportList(CashDropMixin, ListView):
    template_name = "organization/daily_sales_report.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        date_filter = self.request.GET.get('date_filter')

        if date_filter:

            queryset = CashDrop.objects.filter(datetime__startswith=date_filter).order_by('-datetime')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_filter'] = self.request.GET.get('date_filter')
        return context

# class CashDropMixin(IsAdminOrAccountingMixin):
#     model = CashDrop
#     paginate_by = 5
#     queryset = CashDrop.objects.all().order_by('-datetime')

    

# class DailyEndDayReportList(CashDropMixin, ListView):
#     template_name = "organization/daily_sales_report.html"

  
    # def get(self, request):
    #     reports = CashDrop.objects.all().order_by('-datetime')
    #     return render(request, 'organization/daily_sales_report.html', {'object_list': reports})

from django.forms import modelformset_factory
from django.urls import reverse
from django.http import HttpResponseRedirect

TableFormSet = modelformset_factory(Table, form=TableForm, extra=5)
from django.shortcuts import render, redirect
def create_multiple_tables(request):
    if request.method == "POST":
        formset = TableFormSet(request.POST, queryset=Table.objects.none())
        if formset.is_valid():
            formset.save()
            # return redirect('table_list')  # Redirect to a success page
            url = reverse('org:table_list')  # Assuming 'table_list' is the correct URL name
            return HttpResponseRedirect(url)
    else:
        formset = TableFormSet(queryset=Table.objects.none())

    return render(request, "create_multiple_tables.html", {"formset": formset})


TerminalFormSet = modelformset_factory(Terminal, form=TerminalForm, extra=7)
from django.shortcuts import render, redirect
def create_multiple_terminals(request):
    if request.method == "POST":
        formset = TerminalFormSet(request.POST, queryset=Terminal.objects.none())
        if formset.is_valid():
            formset.save()
            # return redirect('table_list')  # Redirect to a success page
            url = reverse('org:terminal_list')  # Assuming 'table_list' is the correct URL name
            return HttpResponseRedirect(url)
    else:
        formset = TerminalFormSet(queryset=Terminal.objects.none())

    return render(request, "create_multiple_terminal.html", {"formset": formset})

# class TableCreate(TableMixin, CreateView):
#     template_name = "create.html"

