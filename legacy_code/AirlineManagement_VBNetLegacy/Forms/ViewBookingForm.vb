Imports System.Windows.Forms

Public Class ViewBookingForm
    Inherits Form

    Private booking As Booking
    Private flight As Flight
    Private lblDetails As Label
    Private btnEdit As Button
    Private btnClose As Button

    Public Sub New(selectedBookingId As Integer)
        InitializeComponent()
        LoadBooking(selectedBookingId)
    End Sub

    Private Sub InitializeComponent()
        Me.Text = "Booking Details"
        Me.Size = New Size(500, 450)
        Me.StartPosition = FormStartPosition.CenterScreen
        Me.FormBorderStyle = FormBorderStyle.FixedDialog
        Me.MaximizeBox = False

        lblDetails = New Label()
        lblDetails.Location = New Point(20, 20)
        lblDetails.Size = New Size(450, 350)
        lblDetails.AutoSize = False
        Me.Controls.Add(lblDetails)

        btnEdit = New Button()
        btnEdit.Text = "Edit"
        btnEdit.Location = New Point(20, 380)
        btnEdit.Size = New Size(150, 30)
        AddHandler btnEdit.Click, AddressOf BtnEdit_Click
        Me.Controls.Add(btnEdit)

        btnClose = New Button()
        btnClose.Text = "Close"
        btnClose.Location = New Point(320, 380)
        btnClose.Size = New Size(150, 30)
        AddHandler btnClose.Click, AddressOf BtnClose_Click
        Me.Controls.Add(btnClose)
    End Sub

    Private Sub LoadBooking(bookingId As Integer)
        booking = BookingRepository.GetById(bookingId)
        If booking Is Nothing Then
            MessageBox.Show("Booking not found.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            Me.Close()
            Return
        End If

        If SessionManager.IsAuthenticated() AndAlso booking.UserId.HasValue AndAlso booking.UserId.Value <> SessionManager.CurrentUser.Id Then
            MessageBox.Show("Access denied. You can only view your own bookings.", "Access Denied", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            Me.Close()
            Return
        End If

        flight = FlightRepository.GetById(booking.FlightId)

        lblDetails.Text = "Booking ID: #" & booking.Id & vbCrLf &
                         "Flight Number: " & flight.FlightNumber & vbCrLf &
                         "Route: " & flight.Origin & " → " & flight.Destination & vbCrLf &
                         "Departure Date: " & flight.DepartureDate.ToString("yyyy-MM-dd") & vbCrLf &
                         "Departure Time: " & flight.DepartureTime.ToString("hh\:mm") & vbCrLf &
                         "Arrival Time: " & flight.ArrivalTime.ToString("hh\:mm") & vbCrLf &
                         "Passenger Name: " & booking.PassengerName & vbCrLf &
                         "Passenger Email: " & booking.PassengerEmail & vbCrLf &
                         "Seat Number: " & If(String.IsNullOrEmpty(booking.SeatNumber), "N/A", booking.SeatNumber) & vbCrLf &
                         "Price: " & flight.Price.ToString("C") & vbCrLf &
                         "Booking Date: " & booking.BookingDate.ToString("yyyy-MM-dd HH:mm")
    End Sub

    Private Sub BtnEdit_Click(sender As Object, e As EventArgs)
        Me.Hide()
        Dim editForm As New EditBookingForm(booking.Id)
        editForm.ShowDialog()
        Me.Close()
    End Sub

    Private Sub BtnClose_Click(sender As Object, e As EventArgs)
        Me.Close()
    End Sub
End Class

