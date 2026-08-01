package com.example.bank.infrastructure

import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewView
import com.example.bank.domain.query.AccountTier
import org.springframework.stereotype.Component

@Component
class AccountOverviewQueryJpaAdapter(
    private val accounts: AccountJpaRepository,
) : AccountOverviewQuery {

    override fun findByAccountId(accountId: String): AccountOverviewView? =
        accounts.findById(accountId)
            .map(::toOverview)
            .orElse(null)

    private fun toOverview(account: AccountJpaEntity): AccountOverviewView =
        AccountOverviewView(
            accountId = account.accountId,
            balance = account.balance,
            tier = AccountTier.forBalance(account.balance),
        )
}
