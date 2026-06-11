package banking.application

import banking.domain.models.account.AccountRepository

class InterestUseCase(
    private val accounts: AccountRepository,
) {
    fun accrueMonthlyInterest(accountId: String): Long {
        val account = accounts.findById(accountId)
        val interest = (account.balance() * 0.035 / 12).toLong()
        account.deposit(interest)
        accounts.save(account)
        return account.balance()
    }
}
