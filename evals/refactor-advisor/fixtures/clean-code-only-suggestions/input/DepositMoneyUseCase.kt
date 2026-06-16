package banking.application

import banking.domain.models.account.AccountRepository
import banking.domain.models.Money

class DepositMoneyUseCase(
    private val accounts: AccountRepository,
) {
    fun execute(accountId: String, amount: Money): Money {
        val account = accounts.findById(accountId)
        account.deposit(amount)
        accounts.save(account)
        return account.balance()
    }
}
