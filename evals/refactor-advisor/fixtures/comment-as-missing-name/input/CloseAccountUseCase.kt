package banking.application

import banking.domain.models.account.AccountRepository

class CloseAccountUseCase(
    private val accounts: AccountRepository,
) {
    fun execute(accountId: String): Boolean {
        val account = accounts.findById(accountId)

        // account can only be closed when it is empty and not frozen
        if (account.balance() == 0L && !account.isFrozen() && account.pendingTransactions() == 0) {
            account.close()
            accounts.save(account)
            return true
        }
        return false
    }
}
