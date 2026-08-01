package com.example.bank.application

import com.example.bank.domain.models.account.BankAccountRepository
import java.math.BigDecimal

class WithdrawMoneyUseCase(
    private val accounts: BankAccountRepository,
) {
    fun execute(accountId: String, amount: BigDecimal): BigDecimal {
        val account = accounts.findById(accountId)
        account.withdraw(amount)
        accounts.save(account)
        return account.balance
    }
}
