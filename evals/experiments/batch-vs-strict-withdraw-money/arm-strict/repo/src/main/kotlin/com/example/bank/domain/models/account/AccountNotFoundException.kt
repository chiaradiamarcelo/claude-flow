package com.example.bank.domain.models.account

class AccountNotFoundException(accountId: String) :
    RuntimeException("No account found with id $accountId")
