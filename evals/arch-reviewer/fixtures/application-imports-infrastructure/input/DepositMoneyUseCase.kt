package banking.application

import banking.domain.models.account.Account
import banking.infrastructure.AccountPostgresAdapter

class DepositMoneyUseCase(
    private val accounts: AccountPostgresAdapter,
) {
    fun execute(accountId: String, amountCents: Long): Long {
        val account: Account = accounts.findById(accountId)
        account.deposit(amountCents)
        accounts.save(account)
        return account.balance()
    }
}
