package com.example.bank.domain.models.account

import java.math.BigDecimal

class InsufficientFundsException(accountId: String, amount: BigDecimal, balance: BigDecimal) :
    RuntimeException("Account $accountId cannot withdraw $amount: balance is $balance")
