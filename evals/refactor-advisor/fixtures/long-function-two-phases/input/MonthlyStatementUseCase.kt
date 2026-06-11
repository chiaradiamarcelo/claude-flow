package banking.application

import banking.domain.models.account.AccountRepository
import banking.domain.query.TransactionHistoryQuery

class MonthlyStatementUseCase(
    private val accounts: AccountRepository,
    private val history: TransactionHistoryQuery,
) {
    fun generate(accountId: String, month: Int): String {
        val account = accounts.findById(accountId)
        val transactions = history.forAccount(accountId).filter { it.month == month }
        var credits = 0L
        var debits = 0L
        for (t in transactions) {
            if (t.amountCents >= 0) credits += t.amountCents else debits += -t.amountCents
        }
        val opening = account.balance() - credits + debits
        val closing = account.balance()

        val builder = StringBuilder()
        builder.append("Statement for ").append(accountId).append(" month ").append(month).append("\n")
        builder.append("Opening balance: ").append(opening).append("\n")
        for (t in transactions) {
            builder.append(t.date).append(" ").append(t.description).append(" ").append(t.amountCents).append("\n")
        }
        builder.append("Total credits: ").append(credits).append("\n")
        builder.append("Total debits: ").append(debits).append("\n")
        builder.append("Closing balance: ").append(closing).append("\n")
        return builder.toString()
    }
}
