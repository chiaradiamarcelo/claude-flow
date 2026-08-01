package com.example.bank.domain.models.account

import java.math.BigDecimal

class InvalidWithdrawalAmountException(amount: BigDecimal) :
    RuntimeException("Withdrawal amount must be strictly positive but was $amount")
