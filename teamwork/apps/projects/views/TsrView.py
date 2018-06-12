from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from teamwork.apps.projects.forms import TSR
from teamwork.apps.courses.models import Course, Assignment

@login_required
def tsr_update(request, slug, assslug):
    """
    public method that takes in a slug and generates a TSR
    form for user. Different form generated based on which
    button was pressed (scrum/normal)
    """
    page_name = "TSR Update"
    page_description = "Update TSR form"
    title = "TSR Update"

    user = request.user
    cur_proj = get_object_or_404(Project.objects.prefetch_related('course'), slug=slug)
    course = cur_proj.course.first()
    asg = get_object_or_404(Assignment, slug=assslug)
    today = datetime.now().date()
    members = cur_proj.members.all()
    emails = list()
    for member in members:
        emails.append(member.email)

    params = str(request)
    if "scrum_master_form" in params:
        scrum_master = True
    else:
        scrum_master = False

    late = False

    asg_ass_date = asg.ass_date

    asg_due_date = asg.due_date
    if asg_ass_date <= today <= asg_due_date:
        late = False
    else:
        late=True


    forms =list()
    if request.method == 'POST':

        for email in emails:
            # grab form
            form = TSR(request.user.id, request.POST, members=members,
                emails=emails, prefix=email, scrum_master=scrum_master)
            if form.is_valid():
                tsr = Tsr()
                tsr.ass_number = asg.ass_number
                tsr.percent_contribution = form.cleaned_data.get('perc_contribution')
                tsr.positive_feedback = form.cleaned_data.get('pos_fb')
                tsr.negative_feedback = form.cleaned_data.get('neg_fb')
                tsr.tasks_completed = form.cleaned_data.get('tasks_comp')
                tsr.performance_assessment = form.cleaned_data.get('perf_assess')
                tsr.notes = form.cleaned_data.get('notes')
                tsr.evaluator = request.user
                tsr.evaluatee =  User.objects.filter(email__iexact=email).first()
                tsr.late = late

                tsr.save()

                # gets fields variables and saves them to project
                cur_proj.tsr.add(tsr)
                cur_proj.save()
                asg.subs.add(tsr)
                asg.save()

        return redirect(view_one_project, slug)

    else:
        # if request was not post then display forms
        for m in emails:
            form_i=TSR(request.user.id, request.POST, members=members,
             emails=emails, prefix=m, scrum_master=scrum_master)
            forms.append(form_i)
        form = TSR(request.user.id, request.POST, members=members,
            emails=emails, scrum_master=scrum_master)

    return render(request, 'projects/tsr_update.html',
    {'forms':forms,'cur_proj': cur_proj, 'ass':asg,
    'page_name' : page_name, 'page_description': page_description,
    'title': title})

@login_required
def tsr_edit(request, slug, assslug):
    """
    public method that takes in a slug and generates a TSR
    form for user. Different form generated based on which
    button was pressed (scrum/normal)
    """
    page_name = "TSR Edit"
    page_description = "Edit TSR form"
    title = "TSR Edit"

    user = request.user
    cur_proj = get_object_or_404(Project, slug=slug)
    course = Course.objects.get(projects=cur_proj)
    asg = get_object_or_404(Assignment, slug=assslug)
    today = datetime.now().date()
    members = cur_proj.members.all()
    emails = list()
    for member in members:
        emails.append(member.email)

    params = str(request)
    if "scrum_master_form" in params:
        scrum_master = True
    else:
        scrum_master = False

    late = False
    if "tsr" in asg.ass_type.lower():
        asg_ass_date = asg.ass_date
        asg_ass_date = datetime.strptime(asg_ass_date,"%Y-%m-%d").date()

        asg_due_date = asg.due_date
        asg_due_date = datetime.strptime(asg_due_date,"%Y-%m-%d").date()
        if asg_ass_date <= today <= asg_due_date:
            late = False
        else:
            late=True

    forms =list()
    if request.method == 'POST':
        for email in emails:
            # grab form
            form = TSR(request.user.id, request.POST, members=members,
                emails=emails, prefix=email, scrum_master=scrum_master)
            if form.is_valid():
                tsr = Tsr()
                tsr.ass_number = asg.ass_number
                tsr.percent_contribution = form.cleaned_data.get('perc_contribution')
                tsr.positive_feedback = form.cleaned_data.get('pos_fb')
                tsr.negative_feedback = form.cleaned_data.get('neg_fb')
                tsr.tasks_completed = form.cleaned_data.get('tasks_comp')
                tsr.performance_assessment = form.cleaned_data.get('perf_assess')
                tsr.notes = form.cleaned_data.get('notes')
                tsr.evaluator = request.user
                tsr.evaluatee =  User.objects.filter(email__iexact=email).first()
                tsr.late = late

                tsr.save()

                # gets fields variables and saves them to project
                cur_proj.tsr.add(tsr)
                cur_proj.save()
                asg.subs.add(tsr)
                asg.save()

        return redirect(view_one_project, slug)

    else:
        # if request was not post then display forms
        for m in emails:
            form_i = TSR(request.user.id, request.POST, members=members,
            emails = emails, prefix=m, scrum_master=scrum_master)
            forms.append(form_i)
        form = TSR(request.user.id, request.POST, members=members,
            emails=emails, scrum_master=scrum_master)

    return render(request, 'projects/tsr_update.html',
    {'forms':forms,'cur_proj': cur_proj, 'ass':asg,
    'page_name' : page_name, 'page_description': page_description,
    'title': title})


@login_required
def view_tsr(request, slug):
    """
    public method that takes in a slug and generates a view for
    submitted TSRs
    """
    page_name = "View TSR"
    page_description = "Submissions"
    title = "View TSR"

    project = get_object_or_404(Project, slug=slug)
    tsrs = list(project.tsr.all())
    members = project.members.all()


    # put emails into list
    emails=list()
    for member in members:
        emails.append(member.email)

    # for every sprint, get the tsr's and calculate the average % contribution
    tsr_dicts=list()
    tsr_dict = list()
    sprint_numbers=Tsr.objects.values_list('ass_number',flat=True).distinct()
    for i in sprint_numbers.all():
        #averages=list()
        tsr_dict=list()
        for member in members:
            tsr_single=list()
            # for every member in project, filter query using member.id
            # and assignment number
            for member_ in members:
                if member == member_:
                    continue
                tsr_query_result=Tsr.objects.filter(evaluatee_id=member.id).filter(evaluator_id=member_.id).filter(ass_number=i).all()
                result_size = len(tsr_query_result)
                if(result_size == 0):
                    continue
                tsr_single.append(tsr_query_result[result_size - 1])

            avg=0

            if tsr_single:
                for tsr_obj in tsr_single:
                    # print("\n\n%d\n\n"%tsr_obj.percent_contribution)
                    avg = avg + tsr_obj.percent_contribution
                avg = avg / len(tsr_single)

            tsr_dict.append({'email':member.email, 'tsr' :tsr_single,'avg' : avg})
            averages.append({'email':member.email,'avg':avg})

        tsr_dicts.append({'number': i , 'dict':tsr_dict,
            'averages':averages})

    med = 1
    if len(members):
        med = int(100/len(members))

    mid = {'low' : int(med*0.7), 'high' : int(med*1.4)}


    if request.method == 'POST':
        return redirect(view_projects)
    return render(request, 'projects/view_tsr.html', {'page_name' : page_name, 'page_description': page_description, 'title': title, 'tsrs' : tsr_dicts, 'contribute_levels' : mid, 'avg':averages})