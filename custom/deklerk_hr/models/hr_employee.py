# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

BIRTHDAY_NOTICE_DAYS = 7
JUBILEE_NOTICE_DAYS = 30
JUBILEE_MONTHS = (150, 300, 480)  # 12.5, 25 and 40 years of service
SALARY_NOTICE_DAYS = 30
CERTIFICATE_NOTICE_DAYS = 60


def _eur(amount):
    """Dutch notation: € 4.350,00"""
    return "€ " + f"{amount:,.2f}".translate(str.maketrans(",.", ".,"))


def _next_anniversary(day, today):
    """Next occurrence of day's month/day on or after today (29 Feb falls on 28 Feb in other years)."""
    for year in (today.year, today.year + 1):
        try:
            candidate = day.replace(year=year)
        except ValueError:
            candidate = date(year, 2, 28)
        if candidate >= today:
            return candidate


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _cron_klerk_hr_signals(self):
        today = fields.Date.context_today(self)
        for employee in self.search([]):
            for deadline, summary in employee._klerk_hr_signals(today):
                employee._klerk_schedule_signal(deadline, summary)

    def _klerk_hr_signals(self, today):
        """(deadline, summary) for every signal that is due for this employee."""
        self.ensure_one()
        signals = []
        if self.birthday:
            birthday = _next_anniversary(self.birthday, today)
            if birthday <= today + relativedelta(days=BIRTHDAY_NOTICE_DAYS):
                age = birthday.year - self.birthday.year
                signals.append(
                    (
                        birthday,
                        self.env._(
                            "Verjaardag %(name)s (%(age)s jaar)",
                            name=self.name,
                            age=age,
                        ),
                    )
                )
        if self.first_contract_date:
            for months in JUBILEE_MONTHS:
                jubilee = self.first_contract_date + relativedelta(months=months)
                if today <= jubilee <= today + relativedelta(days=JUBILEE_NOTICE_DAYS):
                    years = f"{months / 12:g}".replace(".", ",")
                    signals.append(
                        (
                            jubilee,
                            self.env._(
                                "Jubileum %(name)s: %(years)s jaar in dienst",
                                name=self.name,
                                years=years,
                            ),
                        )
                    )
        versions = self.version_ids.sorted("date_version")
        for previous, version in zip(versions, versions[1:], strict=False):
            if (
                version.wage != previous.wage
                and today
                <= version.date_version
                <= today + relativedelta(days=SALARY_NOTICE_DAYS)
            ):
                signals.append(
                    (
                        version.date_version,
                        self.env._(
                            "Salariswijziging %(name)s per %(date)s: %(old)s → %(new)s",
                            name=self.name,
                            date=version.date_version.strftime("%d-%m-%Y"),
                            old=_eur(previous.wage),
                            new=_eur(version.wage),
                        ),
                    )
                )
        for skill in self.employee_skill_ids.filtered(
            lambda s: s.skill_type_id.is_certification and s.valid_to
        ):
            if (
                today
                <= skill.valid_to
                <= today + relativedelta(days=CERTIFICATE_NOTICE_DAYS)
            ):
                signals.append(
                    (
                        skill.valid_to,
                        self.env._(
                            "Certificaat %(cert)s van %(name)s verloopt op %(date)s",
                            cert=skill.skill_id.name,
                            name=self.name,
                            date=skill.valid_to.strftime("%d-%m-%Y"),
                        ),
                    )
                )
        return signals

    def _klerk_schedule_signal(self, deadline, summary):
        """One to-do per signal for the HR responsible; the summary makes the cron idempotent."""
        self.ensure_one()
        exists = self.env["mail.activity"].search_count(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("summary", "=", summary),
            ],
            limit=1,
        )
        if not exists:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                date_deadline=deadline,
                summary=summary,
                user_id=(self.hr_responsible_id or self.env.ref("base.user_admin")).id,
            )
