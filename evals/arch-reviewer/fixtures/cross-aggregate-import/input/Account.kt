package banking.domain.models.account

import banking.domain.models.loan.Loan

class Account(
    val id: String,
    private var balanceCents: Long,
) {
    fun balance(): Long = balanceCents

    fun applyLoanProceeds(loan: Loan) {
        balanceCents += loan.principalCents()
    }
}
