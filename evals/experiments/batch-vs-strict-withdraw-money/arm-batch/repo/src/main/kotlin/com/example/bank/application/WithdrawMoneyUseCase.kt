package com.example.bank.application

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.AccountRepository
import java.math.BigDecimal

class WithdrawMoneyUseCase(
    private val accountRepository: AccountRepository,
) {

    fun execute(accountId: String, amount: BigDecimal): Account {
        val account = accountRepository.findById(accountId)
            ?: throw AccountNotFoundException(accountId)

        val withdrawn = account.withdraw(amount)
        accountRepository.save(withdrawn)

        return withdrawn
    }
}
