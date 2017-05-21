from django import forms
from django.forms import ModelForm, HiddenInput

from survey.models import Commutersurvey, Employer, Team, Leg, MonthlyQuestion

from survey.models import Commutersurvey, Employer, Team, Leg, QuestionOfTheMonth
from survey.utils import *
from django.forms.models import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.db.models import Q

from django.forms.util import ErrorList
from django.forms.widgets import HiddenInput

from datetime import datetime

# CUSTOM WIDGETS
# Move this to a widgets.py file if there are more than a couple


from django.utils.safestring import mark_safe

class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))



class subteamSelectWidget(forms.Select):
    """
    Modification of Select widget: add the team's parent Employer
    via a data-parent attribute on rendering <option>
    """
    def __init__(self, attrs={'class': 'form-control'}, choices=()):
        super(subteamSelectWidget, self).__init__(attrs, choices)

    def render_option(self, selected_choices, option_value, option_label):
        result = super(subteamSelectWidget, self).render_option(selected_choices,
                                                             option_value, option_label)
        if option_value:
            parentid = Team.objects.get(pk=option_value).parent.id
        else:
            parentid = 'blank'
        open_tag_end = result.index('>')
        result = result[:open_tag_end] + ' data-parent="{}"'.format(parentid) + \
            result[open_tag_end:]

        return result


class AlertErrorList(ErrorList):
    """define custom formatting for the leg errors"""
    def __unicode__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return u''
        #FIXME: will this even work as intended?
        for error in self:
            return (u'<div class="alert alert-danger dangerous" '
                    'role="alert">%s</div>' % error)

class CommuterForm(ModelForm):
    class Meta:
        model = Commutersurvey
        fields = ['name', 'email', 'home_address', 'work_address',
                  'employer']
        if not datetime.now().month < 1 or datetime.now().month > 12:
            fields.append('team')
            widgets = {
                'team': subteamSelectWidget()
            }

    def __init__(self, *args, **kwargs):
        super(CommuterForm, self).__init__(*args, **kwargs)

        if datetime.now().month < 1 or datetime.now().month > 12:
            # it's not a challenge!
            self.fields['employer'].queryset = Employer.objects.filter(nochallenge=True)
            self.fields['employer'].help_text = (
                "Use 'Not employed', 'Self',"
                " 'Student' or 'Other employer' as appropriate")
            self.fields['employer'].label = "Employer"
        else:
            # we're in a challenge
            companies = Employer.objects.filter(Q(nochallenge=True) | Q(active2017=True))
            self.fields['employer'].queryset = companies
            self.fields['team'].queryset = Team.objects.filter(
                parent__in=companies)
            self.fields['employer'].help_text = (
                "Use 'Not employed', 'Self',"
                " 'Student', or 'Other employer not in the"
                " Corporate Challenge' as appropriate")
            self.fields['team'].label = "Sub-team"
            self.fields['team'].help_text = (
                "If your company has participating "
                "sub-teams you must choose a sub-team.")

        self.fields['home_address'].help_text = (
        	"Or nearby intersection. "
        	"(<b>INCLUDE ZIPCODE</b>)")
        self.fields['work_address'].help_text = (
        	"Or, if you do not commute to work, "
        	"other destination. (<b>INCLUDE ZIPCODE</b>)")

        # add CSS classes for bootstrap
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['home_address'].widget.attrs['class'] = 'form-control'
        self.fields['work_address'].widget.attrs['class'] = 'form-control'
        self.fields['employer'].widget.attrs['class'] = 'form-control'

        self.fields['home_address'].error_messages['required'] = (
           'Please enter a home address.')
        self.fields['work_address'].error_messages['required'] = (
            'Please enter an address.')
        self.fields['employer'].error_messages['required'] = (
            'Please pick an option from the list.')
        self.fields['email'].error_messages['required'] = (
            'Please enter an email address.')

        if 'team' in self.fields:
        	self.fields['team'].required = False
"""
class ExtraCommuterForm(ModelForm):
    class Meta:
        model = Commutersurvey
        fields = ['comments', 'share']

        # TODO: Take into account day and not just month
        if not datetime.now().month < 1 or datetime.now().month > 12:
            fields = ['share'] + fields

    def __init__(self, *args, **kwargs):
        super(ExtraCommuterForm, self).__init__(*args, **kwargs)

        if 'share' in self.fields:
            self.fields['share'].label = (
                "Please don't share my identifying information with my employer")

        try:
            current_question = QuestionOfTheMonth.objects.get(wr_day_month=current_or_next_month())
            form_question = 'Question of the Month: ' + current_question.value
        except:
            form_question = 'Comment'

        self.fields['comments'].label = form_question
        self.fields['comments'].widget.attrs['rows'] = 4
        self.fields['comments'].widget.attrs['class'] = 'form-control'
"""

class ExtraCommuterForm(forms.Form):

    class Meta:

        fields = ['questionOne','questionTwo', 'questionThree', 'questionFour', 'questionFive',
                   'share', 'comments']

    def __init__(self, *args, **kwargs):
        super(ExtraCommuterForm, self).__init__(*args, **kwargs)


        self.fields['share'] = forms.BooleanField("Please don't share my identifying information with my employer")

        self.fields['comments'] = forms.CharField(widget=forms.Textarea)


        self.fields['questionOne'] = forms.CharField(widget=forms.Textarea)
        self.fields['questionTwo'] = forms.CharField(widget=forms.Textarea)
        self.fields['questionThree'] = forms.CharField(widget=forms.Textarea)
        self.fields['questionFour'] = forms.CharField(widget=forms.Textarea)
        self.fields['questionFive'] = forms.CharField(widget=forms.Textarea)

        arr = ['questionOne','questionTwo', 'questionThree', 'questionFour', 'questionFive']


        index = 0

        now = datetime.now()

        for title in arr:

            index += 1

            questionAnswers = []
            try:
                questionObject = MonthlyQuestion.objects.get(wr_day_month=current_or_next_month(), questionNumber=index)
                questionText = questionObject.question
            except:
                self.fields[arr[index - 1]] = None
                continue

            questionType = questionObject.questionType


            if questionObject.answer_1:
                questionAnswers.append((questionObject.answer_1, questionObject.answer_1))

            if questionObject.answer_2:
                questionAnswers.append((questionObject.answer_2, questionObject.answer_2))

            if questionObject.answer_3:
                questionAnswers.append((questionObject.answer_3, questionObject.answer_3))

            if questionObject.answer_4:
                questionAnswers.append((questionObject.answer_4, questionObject.answer_4))

            if questionObject.answer_5:
                questionAnswers.append((questionObject.answer_5, questionObject.answer_5))

            if questionObject.answer_6:
                questionAnswers.append((questionObject.answer_6, questionObject.answer_6))

            if questionObject.answer_7:
                questionAnswers.append((questionObject.answer_7, questionObject.answer_7))

            if questionObject.answer_8:
                questionAnswers.append((questionObject.answer_8, questionObject.answer_8))

            if questionObject.answer_9:
                questionAnswers.append((questionObject.answer_9, questionObject.answer_9))

            if questionObject.answer_10:
                questionAnswers.append((questionObject.answer_10, questionObject.answer_10))

            if questionObject.answer_11:
                questionAnswers.append((questionObject.answer_11, questionObject.answer_11))

            if questionObject.answer_12:
                questionAnswers.append((questionObject.answer_12, questionObject.answer_12))

            if questionObject.answer_13:
                questionAnswers.append((questionObject.answer_13, questionObject.answer_13))

            if questionObject.answer_14:
                questionAnswers.append((questionObject.answer_14, questionObject.answer_14))

            if questionObject.answer_15:
                questionAnswers.append((questionObject.answer_15, questionObject.answer_15))


            if(questionType == 1):

                questionAnswers.insert(0,('', '-----'))

                self.fields[arr[index - 1]] = forms.MultipleChoiceField(
                    label=questionText,
                    required=False,
                    widget=forms.Select,
                    choices=questionAnswers,
                )

            elif(questionType == 2):

                self.fields[arr[index - 1]] = forms.MultipleChoiceField(
                    label=questionText,
                    required=False,
                    widget=forms.RadioSelect,
                    choices=questionAnswers,
                )


            elif(questionType == 3):

                self.fields[arr[index - 1]]= forms.MultipleChoiceField(
                    label=questionText,
                    required=False,
                    widget=forms.RadioSelect(renderer=HorizontalRadioRenderer),
                    choices=questionAnswers,
                )

            elif(questionType == 4):

                self.fields[arr[index - 1]] = forms.MultipleChoiceField(
                    label=questionText,
                    required=False,
                    widget=forms.CheckboxSelectMultiple,
                    choices=questionAnswers,
                )      

            else:
                self.fields[arr[index - 1]] = forms.MultipleChoiceField(
                    label=questionText,
                    required=False,
                    widget=forms.Textarea,
                    choices=questionAnswers,
                )




class RequiredFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(RequiredFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False
            form.error_class = AlertErrorList

def MakeLegForm(day, direction):
    class LegForm(ModelForm):

        class Meta:
            model = Leg
            fields = ['mode', 'duration', 'day', 'direction']

        def __init__(self, *args, **kwargs):
            super(LegForm, self).__init__(*args, **kwargs)

            self.fields['mode'].label = "How you did, or will, travel"
            self.fields['duration'].label = "Minutes"

            self.fields['mode'].widget.attrs['class'] = 'form-control'
            self.fields['duration'].widget.attrs['class'] = 'form-control'
            self.fields['day'].initial = day
            self.fields['direction'].initial = direction
            self.fields['day'].widget = HiddenInput()
            self.fields['direction'].widget = HiddenInput()
            self.fields['duration'].error_messages['max_value'] = (
                'Did you really travel a whole day?')
            self.fields['mode'].error_messages['required'] = (
                'Please tell us how you did, or will, travel.')

    return LegForm


def MakeLegFormThree(day, direction):
    class LegForm(ModelForm):

        class Meta:
            model = Leg
            fields = ['mode', 'duration', 'day', 'direction']

        def __init__(self, *args, **kwargs):
            super(LegForm, self).__init__(*args, **kwargs)

            self.fields['mode'].label = "How you typically travel"
            self.fields['duration'].label = "Minutes"

            self.fields['mode'].widget.attrs['class'] = 'form-control'
            self.fields['duration'].widget.attrs['class'] = 'form-control'
            self.fields['day'].initial = day
            self.fields['direction'].initial = direction
            self.fields['day'].widget = HiddenInput()
            self.fields['direction'].widget = HiddenInput()
            self.fields['duration'].error_messages['max_value'] = (
                'Did you really travel a whole day?')
            self.fields['mode'].error_messages['required'] = (
                'Please tell us how you did, or will, travel.')

    return LegForm


MakeLegs_WRTW = inlineformset_factory(Commutersurvey, Leg, form=MakeLegForm('w','tw'), extra=1, max_num=10, can_delete=True, formset=RequiredFormSet)
MakeLegs_WRFW = inlineformset_factory(Commutersurvey, Leg, form=MakeLegForm('w','fw'),
                                      extra=1, max_num=10, can_delete=True, formset=RequiredFormSet)
MakeLegs_NormalTW = inlineformset_factory(Commutersurvey, Leg, form=MakeLegFormThree('n','tw'),
                                          extra=1, max_num=10, can_delete=True, formset=RequiredFormSet)
MakeLegs_NormalFW = inlineformset_factory(Commutersurvey, Leg, form=MakeLegFormThree('n','fw'),
                                          extra=1, max_num=10, can_delete=True, formset=RequiredFormSet)

class NormalFromWorkSameAsAboveForm(forms.Form):
    widget = forms.RadioSelect(choices=((True, 'YES'), (False, 'NO')))
    label = 'I usually travel the same way as I typically travel TO work, but in reverse.'
    normal_same_as_reverse = forms.BooleanField(widget=widget, initial=True,
                                                label=label, required=False)

class WalkRideFromWorkSameAsAboveForm(forms.Form):
    widget = forms.RadioSelect(choices=((True, 'YES'), (False, 'NO')))
    label = 'I did, or will, travel the same way as I did, or will travel TO work, but in reverse'
    walkride_same_as_reverse = forms.BooleanField(widget=widget, initial=True,
                                                  label=label, required=False)

class NormalIdenticalToWalkrideForm(forms.Form):
    widget = forms.RadioSelect(choices=((True, 'YES'), (False, 'NO')))
    label = 'My normal commute is exactly like my walk/ride day commute.'
    normal_same_as_walkride = forms.BooleanField(widget=widget, initial=True,
                                                 label=label, required=False)
