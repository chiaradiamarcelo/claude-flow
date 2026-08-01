package com.example.bank.api

import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InsufficientFundsException
import com.example.bank.domain.models.account.InvalidWithdrawalAmountException
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.http.converter.HttpMessageNotReadableException
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.RestControllerAdvice

@RestControllerAdvice
class ApiExceptionHandler {

    @ExceptionHandler(AccountNotFoundException::class)
    fun handleAccountNotFound(exception: AccountNotFoundException): ResponseEntity<Unit> =
        ResponseEntity.status(HttpStatus.NOT_FOUND).build()

    @ExceptionHandler(InsufficientFundsException::class, InvalidWithdrawalAmountException::class)
    fun handleInvalidWithdrawal(exception: RuntimeException): ResponseEntity<Unit> =
        ResponseEntity.badRequest().build()

    @ExceptionHandler(HttpMessageNotReadableException::class)
    fun handleUnreadableRequestBody(exception: HttpMessageNotReadableException): ResponseEntity<Unit> =
        ResponseEntity.badRequest().build()

    @ExceptionHandler(Exception::class)
    fun handleUnexpectedFailure(exception: Exception): ResponseEntity<Unit> =
        ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build()
}
