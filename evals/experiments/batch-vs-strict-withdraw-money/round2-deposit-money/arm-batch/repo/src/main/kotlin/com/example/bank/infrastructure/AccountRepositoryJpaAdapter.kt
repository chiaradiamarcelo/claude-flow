package com.example.bank.infrastructure

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountRepository
import org.springframework.stereotype.Repository

@Repository
internal class AccountRepositoryJpaAdapter(
    private val accounts: AccountJpaRepository,
) : AccountRepository {

    override fun findById(accountId: String): Account? =
        accounts.findById(accountId).map(::toAccount).orElse(null)

    override fun save(account: Account): Account =
        toAccount(accounts.save(toEntity(account)))

    private fun toAccount(entity: AccountJpaEntity): Account =
        Account(entity.accountId, entity.balance)

    private fun toEntity(account: Account): AccountJpaEntity =
        AccountJpaEntity(account.accountId, account.balance)
}
