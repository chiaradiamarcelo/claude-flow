package com.example.bank.domain.query.fakes

import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewView

class FakeAccountOverviewQuery : AccountOverviewQuery {

    private val overviewsByAccountId = mutableMapOf<String, AccountOverviewView>()

    fun seed(view: AccountOverviewView) {
        overviewsByAccountId[view.accountId] = view
    }

    override fun findByAccountId(accountId: String): AccountOverviewView? =
        overviewsByAccountId[accountId]
}
