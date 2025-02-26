<template>
  <div class="task-management">
    <el-card class="box-card">
      <el-form :inline="true" :model="searchForm" class="demo-form-inline">
        <el-form-item label="游戏分类">
          <el-select v-model="searchForm.gameType" placeholder="请选择游戏分类">
            <el-option label="全部" value="" />
            <el-option label="游戏A" value="gameA" />
            <el-option label="游戏B" value="gameB" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名">
          <el-input v-model="searchForm.taskName" placeholder="请输入任务名" />
        </el-form-item>
        <el-form-item label="执行周期">
          <el-select v-model="searchForm.frequency" placeholder="请选择执行周期" @change="handleFrequencyChange">
            <el-option label="全部" value="" />
            <el-option label="日" value="day" />
            <el-option label="周" value="week" />
            <el-option label="月" value="month" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="searchForm.frequency === 'week'" label="每周">
          <el-select v-model="searchForm.dayOfWeek" placeholder="请选择每周">
            <el-option label="全部" value="" />
            <el-option label="周一" value="1" />
            <el-option label="周二" value="2" />
            <el-option label="周三" value="3" />
            <el-option label="周四" value="4" />
            <el-option label="周五" value="5" />
            <el-option label="周六" value="6" />
            <el-option label="周日" value="7" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="searchForm.frequency === 'month'" label="每月">
          <el-select v-model="searchForm.dayOfMonth" placeholder="请选择每月">
            <el-option label="全部" value="" />
            <el-option v-for="n in 31" :key="n" :label="n" :value="n" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table
        :data="tableData"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="gameType" label="游戏分类" width="120" />
        <el-table-column prop="taskName" label="任务名" width="180" />
        <el-table-column label="执行周期" width="150">
          <template slot-scope="scope">
            <span>{{ formatFrequency(scope.row.frequency, scope.row.dayOfMonth, scope.row.dayOfWeek, scope.row.time) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="last_run_at"
          label="最近执行时间"
          width="150"
          :formatter="formatDateTime"
          sortable
        />
        <el-table-column prop="last_run_status" label="最近执行状态" width="120">
          <template slot-scope="scope">
            <el-tooltip v-if="scope.row.last_run_status === 'failure'" :content="scope.row.last_run_log" placement="top">
              <el-tag type="danger">Failure</el-tag>
            </el-tooltip>
            <el-tag v-else-if="scope.row.last_run_status === 'success'" type="success">Success</el-tag>
            <el-tag v-else type="info">未运行</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="next_run_at"
          label="下次执行"
          width="150"
          :formatter="formatDateTime"
          sortable
        />
        <el-table-column
          prop="created_at"
          label="创建时间"
          width="150"
          :formatter="formatDateTime"
          sortable
        />
        <el-table-column
          prop="last_modified_at"
          label="最后修改"
          width="150"
          :formatter="formatDateTime"
          sortable
        />
        <el-table-column label="操作" width="250">
          <template slot-scope="scope">
            <el-button size="mini" @click="handleViewSql(scope.row)">查看 SQL</el-button>
            <el-button size="mini" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="mini" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
        <el-button type="danger" :disabled="multipleSelection.length === 0" @click="handleBatchDelete">批量删除</el-button>
        <el-pagination
          :current-page="currentPage"
          :page-sizes="[20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    <el-dialog
      title="SQL 信息"
      :visible.sync="dialogVisible"
      width="80%"
    >
      <el-table
        :data="sqlData"
        style="width: 100%"
      >
        <el-table-column
          prop="db_name"
          label="db_name"
          width="180"
        />
        <el-table-column
          prop="output_sql"
          label="output_sql"
          width="180"
        />
        <el-table-column
          prop="format"
          label="format"
          width="180"
        />
        <el-table-column
          prop="pos"
          label="pos"
          width="180"
        />
        <el-table-column
          prop="transpose"
          label="transpose(Y/N)"
          width="180"
        />
      </el-table>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog
      title="编辑任务"
      :visible.sync="editDialogVisible"
      width="50%"
    >
      <el-alert
        title="如果要修改具体sql代码，请重新新建任务，本页仅支持运行周期相关修改。"
        type="warning"
        icon="el-icon-warning"
        :closable="false"
        style="margin-bottom: 30px;"
      />
      <el-form ref="editForm" :model="editForm" label-width="120px">
        <el-form-item label="游戏分类">
          <el-select v-model="editForm.gameType" placeholder="请选择游戏分类">
            <el-option label="全部" value="" />
            <el-option label="游戏A" value="gameA" />
            <el-option label="游戏B" value="gameB" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名" style="margin-right: 50px;">
          <el-input v-model="editForm.taskName" placeholder="请输入任务名" />
        </el-form-item>
        <el-row>
          <el-col :span="24">
            <el-form-item label="执行周期">
              <el-select v-model="editForm.frequency" placeholder="请选择执行周期" @change="handleEditFrequencyChange">
                <el-option label="全部" value="" />
                <el-option label="日" value="day" />
                <el-option label="周" value="week" />
                <el-option label="月" value="month" />
              </el-select>
              <el-select v-if="editForm.frequency === 'week'" v-model="editForm.dayOfWeek" placeholder="请选择每周" style="margin-left: 10px;">
                <el-option label="全部" value="" />
                <el-option label="周一" value="1" />
                <el-option label="周二" value="2" />
                <el-option label="周三" value="3" />
                <el-option label="周四" value="4" />
                <el-option label="周五" value="5" />
                <el-option label="周六" value="6" />
                <el-option label="周日" value="7" />
              </el-select>
              <el-select v-if="editForm.frequency === 'month'" v-model="editForm.dayOfMonth" placeholder="请选择每月" style="margin-left: 10px;">
                <el-option label="全部" value="" />
                <el-option v-for="n in 31" :key="n" :label="n" :value="n" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="执行时间">
              <el-time-picker
                v-model="editForm.time"
                placeholder="选择时间"
                format="HH:mm"
                value-format="HH:mm"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="submitEditForm">更 新</el-button>
        <el-button @click="handleCancel">取 消</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import moment from 'moment'

export default {
  name: 'TaskManagement',
  data() {
    return {
      searchForm: {
        gameType: '',
        taskName: '',
        frequency: '',
        dayOfWeek: '',
        dayOfMonth: ''
      },
      tableData: [],
      multipleSelection: [],
      currentPage: 1,
      pageSize: 20,
      total: 0,
      dialogVisible: false,
      sqlData: [],
      editDialogVisible: false,
      editForm: {
        gameType: '',
        taskName: '',
        frequency: '',
        time: '',
        dayOfWeek: '',
        dayOfMonth: ''
      },
      sortParams: [
        { field: 'last_run_at', order: 'desc' },
        { field: 'updated_at', order: 'desc' }
      ]
    }
  },
  created() {
    this.fetchTasks()
  },
  methods: {
    // 获取任务列表
    fetchTasks(sortBy = '', sortOrder = '') {
      const params = {
        page: this.currentPage,
        pageSize: this.pageSize,
        gameType: this.searchForm.gameType,
        taskName: this.searchForm.taskName,
        frequency: this.searchForm.frequency,
        dayOfWeek: this.searchForm.dayOfWeek,
        dayOfMonth: this.searchForm.dayOfMonth,
        sortBy: sortBy,
        sortOrder: sortOrder
      }

      // 构建查询字符串
      const queryString = Object.keys(params)
        .filter(key => params[key] !== '')
        .map(key => `${key}=${encodeURIComponent(params[key])}`)
        .join('&')

      const url = `http://localhost:5002/task_management/tasks?${queryString}`

      fetch(url)
        .then(response => {
          if (!response.ok) {
            throw new Error('获取任务列表失败')
          }
          return response.json()
        })
        .then(data => {
          this.tableData = data.tasks
          this.total = data.total
        })
        .catch(error => {
          console.error('获取任务列表失败:', error)
          this.$message.error(`获取任务列表失败: ${error.message}`)
        })
    },

    // 查询按钮点击事件
    onSearch() {
      this.currentPage = 1 // 重置为第一页
      this.fetchTasks()
    },

    // 分页大小变化
    handleSizeChange(size) {
      this.pageSize = size
      this.fetchTasks()
    },

    // 当前页变化
    handleCurrentChange(page) {
      this.currentPage = page
      this.fetchTasks()
    },

    // 频率变化处理
    handleFrequencyChange(value) {
      this.searchForm.dayOfWeek = ''
      this.searchForm.dayOfMonth = ''
    },

    // 编辑表单频率变化处理
    handleEditFrequencyChange(value) {
      this.editForm.dayOfWeek = ''
      this.editForm.dayOfMonth = ''
    },

    // 格式化频率显示
    formatFrequency(frequency, dayOfMonth, dayOfWeek, time) {
      if (frequency === 'day') {
        return `每日 ${time}`
      } else if (frequency === 'week') {
        let dayOfWeekStr = ''
        switch (String(dayOfWeek)) {
          case '1':
            dayOfWeekStr = '一'
            break
          case '2':
            dayOfWeekStr = '二'
            break
          case '3':
            dayOfWeekStr = '三'
            break
          case '4':
            dayOfWeekStr = '四'
            break
          case '5':
            dayOfWeekStr = '五'
            break
          case '6':
            dayOfWeekStr = '六'
            break
          case '7':
            dayOfWeekStr = '日'
            break
        }
        return `每周${dayOfWeekStr} ${time}`
      } else if (frequency === 'month') {
        return `每月${dayOfMonth} 号 ${time}`
      } else {
        return ''
      }
    },

    // 格式化日期时间
    formatDateTime(row, column) {
      const date = row[column.property]
      if (date) {
        return moment(date).format('YYYY-MM-DD HH:mm')
      } else {
        return ''
      }
    },

    // 查看SQL
    handleViewSql(row) {
      this.dialogVisible = true

      console.log('原始行数据:', row)
      console.log('原始ID:', row.id)
      console.log('ID类型:', typeof row.id)

      if (row.originalId) {
        console.log('原始ID字符串:', row.originalId)
      }

      if (row.bigNumberId) {
        console.log('BigNumber ID:', row.bigNumberId.toString())
      }

      // 尝试直接从数据库ID转换
      const taskId = String(row.id)
      console.log('转换后的ID:', taskId)

      // 添加时间戳避免缓存
      const timestamp = new Date().getTime()
      const url = `/task_management/task_sql/${taskId}?_=${timestamp}`
      console.log('查看SQL - 请求 URL:', url)
      console.log('查看SQL - 请求头:', { 'Content-Type': 'application/json' })

      fetch(url)
        .then(response => {
          console.log('查看SQL - SQL响应状态:', response.status)
          if (!response.ok) {
            return response.text().then(text => {
              console.error('SQL响应内容:', text)
              throw new Error('获取SQL信息失败')
            })
          }
          return response.json()
        })
        .then(data => {
          console.log('SQL数据:', data)
          this.sqlData = data

          // 如果数据为空，显示提示信息
          if (Array.isArray(data) && data.length === 0) {
            this.$message.info('该任务没有SQL数据')
          }
        })
        .catch(error => {
          console.error('获取SQL信息失败:', error)
          this.$message.error(`获取SQL信息失败: ${error.message}`)
        })
    },

    // 编辑任务
    handleEdit(row) {
      this.editForm = { ...row } // 复制任务信息到编辑表单
      this.editDialogVisible = true
    },

    // 提交编辑表单
    submitEditForm() {
      this.$refs.editForm.validate(valid => {
        if (valid) {
          const taskId = String(this.editForm.id)
          fetch(`http://localhost:5002/task_management/task/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.editForm)
          })
            .then(response => {
              if (response.ok) {
                this.$message.success('任务更新成功')
                this.editDialogVisible = false
                this.fetchTasks()
              } else {
                response.json().then(errorData => {
                  this.$message.error(errorData.message || '任务更新失败')
                })
              }
            })
            .catch(error => {
              this.$message.error('任务更新失败: ' + error)
            })
        } else {
          return false
        }
      })
    },

    // 取消编辑
    handleCancel() {
      this.editDialogVisible = false
    },

    // 表格选择变化
    handleSelectionChange(val) {
      this.multipleSelection = val
    },

    // 删除任务
    handleDelete(row) {
      this.$confirm('此操作将永久删除该任务, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        fetch(`http://localhost:5002/task_management/task/${this.getTaskId(row)}`, {
          method: 'DELETE'
        })
          .then(response => {
            if (!response.ok) {
              return response.json().then(data => {
                throw new Error(data.message || '删除任务失败')
              })
            }
            return response.json()
          })
          .then(data => {
            this.$message.success(data.message || '删除成功!')
            this.fetchTasks() // 刷新任务列表
          })
          .catch(error => {
            console.error('删除任务失败:', error)
            this.$message.error(`删除任务失败: ${error.message}`)
          })
      }).catch(() => {
        this.$message.info('已取消删除')
      })
    },

    // 批量删除任务
    handleBatchDelete() {
      if (this.multipleSelection.length === 0) {
        this.$message.warning('请至少选择一个任务')
        return
      }

      this.$confirm(`此操作将永久删除选中的 ${this.multipleSelection.length} 个任务, 是否继续?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        const taskIds = this.multipleSelection.map(item => this.getTaskId(item))

        fetch('http://localhost:5002/task_management/tasks/batch_delete', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ taskIds })
        })
          .then(response => {
            if (!response.ok) {
              return response.json().then(data => {
                throw new Error(data.message || '批量删除任务失败')
              })
            }
            return response.json()
          })
          .then(data => {
            this.$message.success(data.message || '批量删除成功!')
            this.fetchTasks() // 刷新任务列表
          })
          .catch(error => {
            console.error('批量删除任务失败:', error)
            this.$message.error(`批量删除任务失败: ${error.message}`)
          })
      }).catch(() => {
        this.$message.info('已取消删除')
      })
    },

    // 获取任务ID
    getTaskId(row) {
      if (row.bigNumberId) {
        return String(row.bigNumberId)
      } else if (row.originalId) {
        return String(row.originalId)
      } else {
        return String(row.id)
      }
    },
    handleSortChange(column, prop, order) {
      this.fetchTasks(prop, order)
    }
  }
}
</script>
