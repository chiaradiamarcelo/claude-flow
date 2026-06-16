package banking.application

import banking.domain.models.account.AccountRepository

class WithdrawMoneyUseCase(
    private val accounts: AccountRepository,
) {
    fun execute(accountId: String, amountCents: Long): Long {
        if (amountCents <= 0) throw IllegalArgumentException("amount must be positive")
        if (amountCents > 1_000_000) throw IllegalArgumentException("amount exceeds per-transaction limit")

        val account = accounts.findById(accountId)
        if (amountCents <= 0) throw IllegalArgumentException("amount must be positive")
        if (amountCents > 1_000_000) throw IllegalArgumentException("amount exceeds per-transaction limit")
        account.withdraw(amountCents)
        accounts.save(account)
        return account.balance()
    }
}
