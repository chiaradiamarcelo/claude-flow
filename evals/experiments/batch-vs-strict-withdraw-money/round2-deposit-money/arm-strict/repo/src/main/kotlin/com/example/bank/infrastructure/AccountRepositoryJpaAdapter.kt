package com.example.bank.infrastructure

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountRepository

class AccountRepositoryJpaAdapter(
    private val accountJpaRepository: AccountJpaRepository,
) : AccountRepository {

    override fun findById(accountId: String): Account? =
        accountJpaRepository.findById(accountId).map(::toAccount).orElse(null)

    override fun save(account: Account): Account =
        toAccount(accountJpaRepository.save(toJpaEntity(account)))

    private fun toAccount(entity: AccountJpaEntity): Account =
        Account(entity.accountId, entity.balance)

    private fun toJpaEntity(account: Account): AccountJpaEntity =
        AccountJpaEntity(account.accountId, account.balance)
}
