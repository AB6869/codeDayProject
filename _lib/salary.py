import logging
from decimal import Decimal


class AgeGroup:
    ONE = "25-27"
    TWO = "28-37"
    THREE = "38-49"
    FOUR = "50-65"
    INELIGEBLE_FOR_PENSION = "0-24,66+"

    @classmethod
    def get(self, age: int) -> str:
        groups = {
            range(25, 27 + 1): AgeGroup.ONE,
            range(28, 37 + 1): AgeGroup.TWO,
            range(38, 49 + 1): AgeGroup.THREE,
            range(50, 65 + 1): AgeGroup.FOUR,
        }
        return next((v for k, v in groups.items() if age in k), AgeGroup.INELIGEBLE_FOR_PENSION)


class SalaryGroups:
    def __init__(self, income_base_amount: int) -> None:
        self.amount_group_one = income_base_amount * Decimal("7.5")
        self.amount_group_two = income_base_amount * Decimal("20")
        self.amount_group_three = income_base_amount * Decimal("30")

    @classmethod
    def get_pension_percentage_group_one(cls, age_group: str) -> Decimal:
        return {
            AgeGroup.ONE: Decimal("0.045"),  # 0.0164
            AgeGroup.TWO: Decimal("0.045"),   # 0.045
            AgeGroup.THREE: Decimal("0.045"),  # 0.07
            AgeGroup.FOUR: Decimal("0.045"),   # 0.07
            AgeGroup.INELIGEBLE_FOR_PENSION: Decimal("0"),
        }[age_group]

    def yearly_pension_cost_group_one(self, yearly_salary: int, age: str) -> Decimal:
        age_group = AgeGroup.get(age)
        percentage = self.get_pension_percentage_group_one(age_group)
        if yearly_salary > self.amount_group_one:
            return self.amount_group_one * percentage
        return yearly_salary * percentage

    @classmethod
    def get_pension_percentage_group_two(cls, age_group: str) -> Decimal:
        return {
            AgeGroup.ONE: Decimal("0.3"),  # 0.0164
            AgeGroup.TWO: Decimal("0.3"),     # 0.3
            AgeGroup.THREE: Decimal("0.3"),  # 0.26
            AgeGroup.FOUR: Decimal("0.3"),   # 0.31
            AgeGroup.INELIGEBLE_FOR_PENSION: Decimal("0"),
        }[age_group]

    def yearly_pension_cost_group_two(self, yearly_salary: int, age: int) -> Decimal:
        age_group = AgeGroup.get(age)
        percentage = self.get_pension_percentage_group_two(age_group)
        if yearly_salary > self.amount_group_two:
            return (self.amount_group_two - self.amount_group_one) * percentage
        if yearly_salary <= self.amount_group_one:
            return 0
        return (yearly_salary - self.amount_group_one) * percentage

    @classmethod
    def get_pension_percentage_group_three(cls, age_group: str) -> Decimal:
        return {
            AgeGroup.ONE: Decimal("0.3"),  # 0.0164
            AgeGroup.TWO: Decimal("0.3"),     # 0.3
            AgeGroup.THREE: Decimal("0.3"),  # 0.17
            AgeGroup.FOUR: Decimal("0.3"),   # 0.25
            AgeGroup.INELIGEBLE_FOR_PENSION: Decimal("0"),
        }[age_group]

    def yearly_pension_cost_group_three(self, yearly_salary: int, age: int) -> Decimal:
        age_group = AgeGroup.get(age)
        percentage = self.get_pension_percentage_group_three(age_group)
        if yearly_salary > self.amount_group_two:
            return (yearly_salary - self.amount_group_two) * percentage
        return 0


class CostPriceCalculator:
    def cost_price(self, monthly_salary: int, age: int, income_base_amount: int):
        calc_cost_price = self.cost_price_monthly_salary(
            monthly_salary, age, income_base_amount
        )
        return calc_cost_price + self.employee_hourly_cost()

    def cost_price_monthly_salary(
        self, monthly_salary: int, age: int, income_base_amount: int
    ) -> int:
        return int(round(self.hourly_cost(monthly_salary, age, income_base_amount), -1))

    def cost_price_hourly_salary(self, hourly_salary: int):
        return int(round(hourly_salary * Decimal("1.12") * (1 + self._employeer_fee_factor()), -1))

    def hourly_cost(self, monthly_salary: int, age: int, income_base_amount: int) -> Decimal:
        return self.yearly_cost(monthly_salary, age, income_base_amount) / self.yearly_working_hours()

    def yearly_cost(self, monthly_salary: int, age: int, income_base_amount: int) -> Decimal:
        yearly_salary = self.yearly_salary(monthly_salary)
        salary_cost = self.yearly_salary_cost(yearly_salary)
        pension_cost = self.yearly_pension_cost(yearly_salary, age, income_base_amount) * (
            1 + self._special_salary_tax_factor()
        )
        return salary_cost + pension_cost

    def yearly_salary(self, monthly_salary: int) -> Decimal:
        return monthly_salary * Decimal("12.2")

    def yearly_salary_cost(self, yearly_salary: int) -> Decimal:
        return yearly_salary * (1 + self._employeer_fee_factor())

    def yearly_pension_cost(self, yearly_salary: int, age: int, income_base_amount: int) -> Decimal:
        salary_groups = SalaryGroups(income_base_amount)
        group_one = salary_groups.yearly_pension_cost_group_one(yearly_salary, age)
        group_two = salary_groups.yearly_pension_cost_group_two(yearly_salary, age)
        group_three = salary_groups.yearly_pension_cost_group_three(yearly_salary, age)
        return group_one + group_two + group_three

    def _employeer_fee_factor(self) -> Decimal:
        return Decimal("0.3142")

    def _special_salary_tax_factor(self) -> Decimal:
        return Decimal("0.2426")

    def yearly_working_hours(self) -> int:
        return 1692

    def employee_hourly_cost(self) -> int:
        return 0

