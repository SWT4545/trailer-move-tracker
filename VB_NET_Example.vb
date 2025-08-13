' VB.NET Example Code for Smith & Williams Trucking API
' This shows how to connect to the Python REST API from VB.NET
' 
' Required: Install Newtonsoft.Json NuGet package:
' Install-Package Newtonsoft.Json

Imports System.Net.Http
Imports System.Text
Imports System.Threading.Tasks
Imports Newtonsoft.Json

' ===== MAIN API CLIENT CLASS =====
Public Class TrailerTrackerAPI
    Private ReadOnly client As HttpClient
    Private ReadOnly baseUrl As String
    Private username As String
    Private password As String
    
    ' Constructor
    Public Sub New(Optional apiUrl As String = "http://localhost:8000")
        baseUrl = apiUrl
        client = New HttpClient()
        client.BaseAddress = New Uri(baseUrl)
    End Sub
    
    ' ===== AUTHENTICATION =====
    Public Async Function Login(user As String, pass As String) As Task(Of LoginResult)
        username = user
        password = pass
        
        ' Create login request
        Dim loginData = New With {
            .username = user,
            .password = pass
        }
        
        Dim json = JsonConvert.SerializeObject(loginData)
        Dim content = New StringContent(json, Encoding.UTF8, "application/json")
        
        Try
            Dim response = Await client.PostAsync("/api/login", content)
            Dim responseJson = Await response.Content.ReadAsStringAsync()
            
            If response.IsSuccessStatusCode Then
                ' Set auth header for future requests
                Dim authValue = Convert.ToBase64String(Encoding.ASCII.GetBytes($"{user}:{pass}"))
                client.DefaultRequestHeaders.Authorization = 
                    New Headers.AuthenticationHeaderValue("Basic", authValue)
                
                Return JsonConvert.DeserializeObject(Of LoginResult)(responseJson)
            Else
                Return New LoginResult With {
                    .success = False,
                    .message = "Login failed"
                }
            End If
        Catch ex As Exception
            Return New LoginResult With {
                .success = False,
                .message = ex.Message
            }
        End Try
    End Function
    
    ' ===== GET ALL TRAILERS =====
    Public Async Function GetTrailers(Optional status As String = Nothing) As Task(Of List(Of Trailer))
        Try
            Dim url = "/api/trailers"
            If Not String.IsNullOrEmpty(status) Then
                url &= $"?status={status}"
            End If
            
            Dim response = Await client.GetAsync(url)
            
            If response.IsSuccessStatusCode Then
                Dim json = Await response.Content.ReadAsStringAsync()
                Dim result = JsonConvert.DeserializeObject(Of TrailerResponse)(json)
                Return result.trailers
            Else
                Return New List(Of Trailer)()
            End If
        Catch ex As Exception
            MessageBox.Show($"Error getting trailers: {ex.Message}")
            Return New List(Of Trailer)()
        End Try
    End Function
    
    ' ===== GET SINGLE TRAILER =====
    Public Async Function GetTrailer(trailerNumber As String) As Task(Of Trailer)
        Try
            Dim response = Await client.GetAsync($"/api/trailers/{trailerNumber}")
            
            If response.IsSuccessStatusCode Then
                Dim json = Await response.Content.ReadAsStringAsync()
                Return JsonConvert.DeserializeObject(Of Trailer)(json)
            Else
                Return Nothing
            End If
        Catch ex As Exception
            Return Nothing
        End Try
    End Function
    
    ' ===== CREATE NEW TRAILER =====
    Public Async Function CreateTrailer(trailer As Trailer) As Task(Of Boolean)
        Try
            Dim json = JsonConvert.SerializeObject(trailer)
            Dim content = New StringContent(json, Encoding.UTF8, "application/json")
            
            Dim response = Await client.PostAsync("/api/trailers", content)
            Return response.IsSuccessStatusCode
        Catch ex As Exception
            Return False
        End Try
    End Function
    
    ' ===== UPDATE TRAILER STATUS =====
    Public Async Function UpdateTrailerStatus(trailerNumber As String, newStatus As String, notes As String) As Task(Of Boolean)
        Try
            Dim updateData = New With {
                .status = newStatus,
                .notes = notes
            }
            
            Dim json = JsonConvert.SerializeObject(updateData)
            Dim content = New StringContent(json, Encoding.UTF8, "application/json")
            
            Dim response = Await client.PutAsync($"/api/trailers/{trailerNumber}/status", content)
            Return response.IsSuccessStatusCode
        Catch ex As Exception
            Return False
        End Try
    End Function
    
    ' ===== GET ALL MOVES =====
    Public Async Function GetMoves(Optional status As String = Nothing, Optional driver As String = Nothing) As Task(Of List(Of Move))
        Try
            Dim url = "/api/moves"
            Dim params = New List(Of String)()
            
            If Not String.IsNullOrEmpty(status) Then params.Add($"status={status}")
            If Not String.IsNullOrEmpty(driver) Then params.Add($"driver={driver}")
            
            If params.Count > 0 Then
                url &= "?" & String.Join("&", params)
            End If
            
            Dim response = Await client.GetAsync(url)
            
            If response.IsSuccessStatusCode Then
                Dim json = Await response.Content.ReadAsStringAsync()
                Dim result = JsonConvert.DeserializeObject(Of MoveResponse)(json)
                Return result.moves
            Else
                Return New List(Of Move)()
            End If
        Catch ex As Exception
            Return New List(Of Move)()
        End Try
    End Function
    
    ' ===== CREATE NEW MOVE =====
    Public Async Function CreateMove(move As Move) As Task(Of Boolean)
        Try
            Dim json = JsonConvert.SerializeObject(move)
            Dim content = New StringContent(json, Encoding.UTF8, "application/json")
            
            Dim response = Await client.PostAsync("/api/moves", content)
            Return response.IsSuccessStatusCode
        Catch ex As Exception
            Return False
        End Try
    End Function
    
    ' ===== ASSIGN DRIVER TO MOVE =====
    Public Async Function AssignDriver(orderNumber As String, driverName As String) As Task(Of Boolean)
        Try
            Dim url = $"/api/moves/{orderNumber}/assign?driver_name={driverName}"
            Dim response = Await client.PutAsync(url, Nothing)
            Return response.IsSuccessStatusCode
        Catch ex As Exception
            Return False
        End Try
    End Function
    
    ' ===== GET DASHBOARD STATS =====
    Public Async Function GetDashboardStats() As Task(Of DashboardStats)
        Try
            Dim response = Await client.GetAsync("/api/dashboard/stats")
            
            If response.IsSuccessStatusCode Then
                Dim json = Await response.Content.ReadAsStringAsync()
                Return JsonConvert.DeserializeObject(Of DashboardStats)(json)
            Else
                Return Nothing
            End If
        Catch ex As Exception
            Return Nothing
        End Try
    End Function
End Class

' ===== DATA MODELS =====
Public Class LoginResult
    Public Property success As Boolean
    Public Property username As String
    Public Property role As String
    Public Property message As String
End Class

Public Class Trailer
    Public Property trailer_number As String
    Public Property trailer_type As String
    Public Property status As String
    Public Property condition As String
    Public Property current_location As String
    Public Property customer_owner As String
    Public Property notes As String
    Public Property last_updated As DateTime
End Class

Public Class TrailerResponse
    Public Property count As Integer
    Public Property trailers As List(Of Trailer)
End Class

Public Class Move
    Public Property order_number As String
    Public Property customer_name As String
    Public Property origin_city As String
    Public Property origin_state As String
    Public Property destination_city As String
    Public Property destination_state As String
    Public Property pickup_date As String
    Public Property delivery_date As String
    Public Property amount As Decimal
    Public Property driver_name As String
    Public Property status As String
End Class

Public Class MoveResponse
    Public Property count As Integer
    Public Property moves As List(Of Move)
End Class

Public Class DashboardStats
    Public Property moves As MoveStats
    Public Property trailers As TrailerStats
    Public Property drivers As DriverStats
End Class

Public Class MoveStats
    Public Property pending As Integer
    Public Property active As Integer
    Public Property completed As Integer
End Class

Public Class TrailerStats
    Public Property available As Integer
    Public Property in_use As Integer
End Class

Public Class DriverStats
    Public Property active As Integer
End Class

' ===== EXAMPLE WINDOWS FORM =====
Public Class MainForm
    Private api As TrailerTrackerAPI
    
    Private Async Sub btnLogin_Click(sender As Object, e As EventArgs) Handles btnLogin.Click
        api = New TrailerTrackerAPI()
        
        ' Login
        Dim result = Await api.Login(txtUsername.Text, txtPassword.Text)
        
        If result.success Then
            MessageBox.Show($"Welcome {result.username}!" & vbCrLf & $"Role: {result.role}")
            
            ' Load dashboard
            Await LoadDashboard()
        Else
            MessageBox.Show("Login failed!")
        End If
    End Sub
    
    Private Async Function LoadDashboard() As Task
        ' Get stats
        Dim stats = Await api.GetDashboardStats()
        
        If stats IsNot Nothing Then
            lblPendingMoves.Text = stats.moves.pending.ToString()
            lblActiveMoves.Text = stats.moves.active.ToString()
            lblCompletedMoves.Text = stats.moves.completed.ToString()
            lblAvailableTrailers.Text = stats.trailers.available.ToString()
        End If
        
        ' Load trailers
        Dim trailers = Await api.GetTrailers()
        DataGridView1.DataSource = trailers
        
        ' Load moves
        Dim moves = Await api.GetMoves()
        DataGridView2.DataSource = moves
    End Function
    
    Private Async Sub btnCreateTrailer_Click(sender As Object, e As EventArgs) Handles btnCreateTrailer.Click
        Dim newTrailer = New Trailer With {
            .trailer_number = txtTrailerNumber.Text,
            .trailer_type = cmbTrailerType.Text,
            .status = "available",
            .condition = "good",
            .current_location = txtLocation.Text,
            .customer_owner = txtCustomer.Text
        }
        
        Dim success = Await api.CreateTrailer(newTrailer)
        
        If success Then
            MessageBox.Show("Trailer created successfully!")
            Await LoadDashboard()
        Else
            MessageBox.Show("Failed to create trailer")
        End If
    End Sub
    
    Private Async Sub btnUpdateStatus_Click(sender As Object, e As EventArgs) Handles btnUpdateStatus.Click
        Dim trailerNumber = InputBox("Enter trailer number:")
        Dim newStatus = InputBox("Enter new status (available/in_use/maintenance):")
        
        Dim success = Await api.UpdateTrailerStatus(trailerNumber, newStatus, "Updated from VB.NET")
        
        If success Then
            MessageBox.Show("Status updated!")
            Await LoadDashboard()
        Else
            MessageBox.Show("Failed to update status")
        End If
    End Sub
    
    Private Async Sub btnAssignDriver_Click(sender As Object, e As EventArgs) Handles btnAssignDriver.Click
        Dim orderNumber = InputBox("Enter order number:")
        Dim driverName = InputBox("Enter driver name:")
        
        Dim success = Await api.AssignDriver(orderNumber, driverName)
        
        If success Then
            MessageBox.Show($"Driver {driverName} assigned to order {orderNumber}")
            Await LoadDashboard()
        Else
            MessageBox.Show("Failed to assign driver")
        End If
    End Sub
End Class

' ===== CONSOLE APP EXAMPLE =====
Module ConsoleExample
    Sub Main()
        RunExample().Wait()
    End Sub
    
    Async Function RunExample() As Task
        Dim api = New TrailerTrackerAPI()
        
        ' Login
        Console.WriteLine("Logging in...")
        Dim loginResult = Await api.Login("Brandon", "owner123")
        
        If loginResult.success Then
            Console.WriteLine($"Logged in as: {loginResult.username} ({loginResult.role})")
            
            ' Get dashboard stats
            Console.WriteLine(vbCrLf & "Dashboard Stats:")
            Dim stats = Await api.GetDashboardStats()
            Console.WriteLine($"  Pending Moves: {stats.moves.pending}")
            Console.WriteLine($"  Active Moves: {stats.moves.active}")
            Console.WriteLine($"  Available Trailers: {stats.trailers.available}")
            
            ' Get trailers
            Console.WriteLine(vbCrLf & "Available Trailers:")
            Dim trailers = Await api.GetTrailers("available")
            For Each trailer In trailers
                Console.WriteLine($"  - {trailer.trailer_number}: {trailer.current_location}")
            Next
            
            ' Get moves
            Console.WriteLine(vbCrLf & "Recent Moves:")
            Dim moves = Await api.GetMoves()
            For Each move In moves.Take(5)
                Console.WriteLine($"  - {move.order_number}: {move.origin_city} to {move.destination_city} ({move.status})")
            Next
        Else
            Console.WriteLine("Login failed!")
        End If
        
        Console.ReadLine()
    End Function
End Module