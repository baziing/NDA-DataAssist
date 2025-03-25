<template>
  <div class="task-management">
    <el-card class="box-card">
      <el-form :inline="true" :model="searchForm" class="demo-form-inline">
        <el-form-item label="游戏分类">
          <el-select v-model="searchForm.gameType" placeholder="请选择游戏分类">
            <el-option
              v-for="item in gameCategories"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
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
            <el-tooltip v-if="scope.row.is_enabled === 0 || scope.row.is_enabled === false" content="任务调度已关闭" placement="top">
              <el-tag type="info">未调度</el-tag>
            </el-tooltip>
            <el-tooltip v-else-if="scope.row.last_run_status === 'failure'" :content="scope.row.last_run_log" placement="top">
              <el-tag type="danger">Failure</el-tag>
            </el-tooltip>
            <el-tag v-else-if="scope.row.last_run_status === 'success'" type="success">Success</el-tag>
            <el-tag v-else type="success">待运行</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="next_run_at"
          label="下次执行"
          width="150"
          :formatter="formatNextRunTime"
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
            <el-button
              type="text"
              size="small"
              @click="handleDownloadReport(scope.row)"
            >下载报表</el-button>
            <el-divider direction="vertical" />
            <el-button
              type="text"
              size="small"
              @click="handleViewSql(scope.row)"
            >查看 SQL</el-button>
            <el-divider direction="vertical" />
            <el-button
              type="text"
              size="small"
              @click="handleEdit(scope.row)"
            >编辑</el-button>
            <el-divider direction="vertical" />
            <el-button
              type="text"
              size="small"
              class="delete-btn"
              @click="handleDelete(scope.row)"
            >删除</el-button>
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
      :visible.sync="dialogVisible"
      width="80%"
    >
      <template slot="title">
        <span>SQL 信息</span>
        <i
          class="el-icon-download"
          style="margin-left: 10px; cursor: pointer; font-size: 16px; color: #409EFF;"
          title="导出 SQL 信息"
          @click="exportSqlInfo"
        />
      </template>
      <el-table
        :data="sqlData"
        class="sql-info-table"
        style="width: 100%"
      >
        <el-table-column
          prop="sheet_name"
          label="sheet_name"
          width="120"
        />
        <el-table-column
          prop="db_name"
          label="db_name"
          width="120"
        />
        <el-table-column
          prop="output_sql"
          label="output_sql"
          width="350"
        />
        <el-table-column
          prop="format"
          label="format"
          width="300"
        />
        <el-table-column
          prop="pos"
          label="pos"
          width="100"
        />
        <el-table-column
          prop="transpose"
          label="transpose(Y/N)"
          width="150"
        >
          <template slot-scope="scope">
            {{ scope.row.transpose === 1 ? 'Y' : (scope.row.transpose === 0 ? 'N' : scope.row.transpose) }}
          </template>
        </el-table-column>
      </el-table>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog
      title="编辑任务"
      :visible.sync="editDialogVisible"
      width="50%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <el-alert
        title="如果要修改具体sql代码，请重新新建任务，本页仅支持运行名称和周期相关修改。"
        type="warning"
        icon="el-icon-warning"
        :closable="false"
        style="margin-bottom: 30px;"
      />
      <el-form ref="editForm" :model="editForm" :rules="editRules" label-width="120px">
        <el-form-item label="游戏分类">
          <el-select v-model="editForm.gameType" placeholder="请选择游戏分类">
            <el-option
              v-for="item in editGameCategories"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名称" prop="taskName" style="margin-right: 50px;">
          <el-input
            v-model="editForm.taskName"
            placeholder="请输入任务名"
            @input="validateTaskName"
            @blur="updateEditOutputExample"
          />
          <div class="form-tip">每个游戏分类下，任务名称不能重名，不支持空格输入；<br>
            支持日期命名，以达到[25M02月度报告.xlsx]效果。具体请见 格式说明-文件名格式化；  </div>
        </el-form-item>
        <el-form-item label="输出示例">
          <span v-if="editOutputExample">{{ editOutputExample }}</span>
          <span v-else>请在上方输入任务名称</span>
        </el-form-item>
        <el-form-item label="设置参数" style="margin-right: 50px;">
          <el-input
            v-model="editForm.settings"
            type="textarea"
            :rows="5"
            placeholder="[可选]输入JSON 格式的参数设置"
          />
          <div class="form-tip">暂仅支持冻结。请输入有效的JSON 格式，例如：{"freeze": [{"title": "整体战力", "config": "B2"}]}</div>
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

        <el-form-item label="执行时间">
          <el-time-picker
            v-model="editForm.time"
            placeholder="选择时间"
            format="HH:mm"
            value-format="HH:mm"
            class="execution-time-picker"
          />
        </el-form-item>

        <!-- 邮件地址选择 -->
        <el-form-item label="邮件地址" style="margin-right: 50px;">
          <el-select
            v-model="editForm.recipients"
            multiple
            filterable
            placeholder="请选择收件人"
            style="width: 100%;"
            @tag-close="handleTagClose"
          >
            <template slot="prefix">
              <i class="el-icon-message" style="color: #909399;" />
            </template>
            <el-option-group label="邮件组">
              <el-option
                v-for="group in emailGroups"
                :key="'group-' + group.id"
                :label="group.group_name"
                :value="'group-' + group.id"
                class="email-group-option"
              >
                <span style="float: left">{{ group.group_name }}</span>
                <span style="float: right; color: #409EFF; font-size: 13px">邮件组</span>
              </el-option>
            </el-option-group>
            <el-option-group label="邮件地址">
              <el-option
                v-for="email in emails"
                :key="'email-' + email.id"
                :label="email.name ? email.name + ' <' + email.email + '>' : email.email"
                :value="'email-' + email.id"
                class="email-address-option"
              >
                <span style="float: left">{{ email.email }}</span>
                <span style="float: right; color: #67C23A; font-size: 13px">个人</span>
              </el-option>
            </el-option-group>
          </el-select>
          <div class="form-tip">可以选择多个邮件组或邮件地址作为收件人</div>
        </el-form-item>
        <!-- 邮件地址选择结束 -->

        <el-form-item label="开启调度" prop="isEnabled">
          <el-switch
            v-model="editForm.isEnabled"
            active-color="#13ce66"
            inactive-color="#ff4949"
          />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" :loading="updating" @click="submitEditForm">更 新</el-button>
        <el-button :disabled="updating" @click="handleCancel">取 消</el-button>
      </span>
    </el-dialog>
    <el-dialog
      title="任务详情"
      :visible.sync="taskDetailVisible"
      width="80%"
    >
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本信息" name="info">
          <!-- 现有的任务信息内容 -->
        </el-tab-pane>
        <el-tab-pane label="SQL信息" name="sql">
          <!-- 现有的SQL信息内容 -->
        </el-tab-pane>
        <el-tab-pane label="生成文件" name="files">
          <el-table
            v-loading="filesLoading"
            :data="taskFiles"
            style="width: 100%"
          >
            <el-table-column
              prop="filename"
              label="文件名"
              min-width="300"
            >
              <template slot-scope="scope">
                <el-link
                  type="primary"
                  @click="downloadFile(scope.row.filename)"
                >
                  {{ scope.row.filename }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column
              prop="created_at"
              label="生成时间"
              width="180"
            />
            <el-table-column
              prop="size"
              label="文件大小"
              width="120"
            >
              <template slot-scope="scope">
                {{ formatFileSize(scope.row.size) }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
    <el-dialog
      title="下载报表"
      :visible.sync="downloadDialogVisible"
      width="60%"
    >
      <el-table
        v-loading="filesLoading"
        :data="taskFiles"
        style="width: 100%"
      >
        <el-table-column
          prop="filename"
          label="文件名"
          min-width="300"
        >
          <template slot-scope="scope">
            <el-link
              type="primary"
              @click="downloadFile(scope.row.filename)"
            >
              {{ scope.row.filename }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="生成时间"
          width="180"
        />
        <el-table-column
          prop="size"
          label="文件大小"
          width="120"
        >
          <template slot-scope="scope">
            {{ formatFileSize(scope.row.size) }}
          </template>
        </el-table-column>
      </el-table>
      <span slot="footer" class="dialog-footer">
        <el-button @click="downloadDialogVisible = false">关闭</el-button>
      </span>
    </el-dialog>
    <DeleteConfirmationDialog
      :visible="deleteConfirmVisible"
      :message="deleteConfirmMessage"
      :loading="deleteConfirmLoading"
      @confirm="handleDeleteConfirm"
      @cancel="deleteConfirmVisible = false"
    />
  </div>
</template>

<script>
import moment from 'moment'
import axios from 'axios'
import settings from '@/settings'
import DeleteConfirmationDialog from '@/components/DeleteConfirmationDialog.vue'
import XLSX from 'xlsx'

export default {
  name: 'TaskManagement',
  components: {
    DeleteConfirmationDialog
  },
  data() {
    return {
      gameCategories: [
        { label: '全部', value: '' },
        ...settings.gameCategories
      ],
      editGameCategories: settings.gameCategories,
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
        dayOfMonth: '',
        isEnabled: true,
        recipients: [],
        settings: ''
      },
      sortParams: [
        { field: 'last_run_at', order: 'desc' },
        { field: 'updated_at', order: 'desc' }
      ],
      updating: false,
      originalTaskName: '',
      taskDetailVisible: false,
      activeTab: 'info',
      taskFiles: [],
      filesLoading: false,
      downloadDialogVisible: false,
      currentTask: null,
      editOutputExample: '',
      deleteConfirmVisible: false,
      deleteConfirmMessage: '',
      deleteConfirmLoading: false,
      taskToDelete: null,
      batchDeleteMode: false,
      emails: [],
      emailGroups: []
    }
  },
  watch: {
    // 监听收件人变化，应用样式
    'editForm.recipients': {
      handler() {
        this.$nextTick(() => {
          this.applyTagStyles()
        })
      },
      deep: true
    }
  },
  created() {
    this.fetchTasks()
    // 获取邮件地址列表
    this.fetchEmails()
    // 获取邮件组列表
    this.fetchEmailGroups()
  },
  mounted() {
    // 组件挂载后应用样式
    this.applyTagStyles()

    // 添加全局点击事件监听器，确保在选择器展开/收起时应用样式
    document.addEventListener('click', this.handleGlobalClick)
  },
  beforeDestroy() {
    // 组件销毁前移除事件监听器
    document.removeEventListener('click', this.handleGlobalClick)
  },
  methods: {
    updateEditOutputExample() {
      if (this.editForm.taskName) {
        fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/format_filename`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ taskName: this.editForm.taskName })
        })
          .then(response => response.json())
          .then(data => {
            this.editOutputExample = data.formatted_filename
          })
          .catch(error => {
            console.error('Error:', error)
            this.editOutputExample = '生成示例失败'
          })
      } else {
        this.editOutputExample = ''
      }
    },
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

      const url = `http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/tasks?${queryString}`

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
        // 将时间转换为西八区 (-8 时区)
        const formattedDate = moment(date).utcOffset(0).format('YYYY-MM-DD HH:mm')
        return formattedDate
      } else {
        return ''
      }
    },

    // 查看SQL
    handleViewSql(row) {
      this.dialogVisible = true
      this.currentTask = row // 保存当前任务信息

      // 尝试直接从数据库ID转换
      const taskId = String(row.id)
      console.log('转换后的ID:', taskId)

      // 添加时间戳避免缓存
      const timestamp = new Date().getTime()
      const url = `http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/task_sql/${taskId}?_=${timestamp}`
      console.log('查看SQL - 请求 URL:', url)

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
      // 清空之前的收件人信息，避免显示上一次的数据
      if (this.editForm) {
        this.editForm.recipients = []
      }

      this.currentTask = row // 保存当前编辑的任务
      this.editForm = {
        ...row,
        isEnabled: row.is_enabled === 1 || row.is_enabled === true,
        recipients: [], // 初始化为空数组，等待异步加载
        settings: '' // 初始化设置字段
      }

      // 从任务数据中获取设置
      try {
        if (row.settings) {
          const settingsObj = typeof row.settings === 'string' ? JSON.parse(row.settings) : row.settings
          this.editForm.settings = JSON.stringify(settingsObj, null, 2)
        }
      } catch (e) {
        console.error('解析设置失败:', e)
        this.editForm.settings = row.settings || ''
      }

      this.originalTaskName = row.taskName
      this.editDialogVisible = true
      this.updateEditOutputExample() // 初始化输出示例

      // 获取任务的收件人信息
      this.fetchTaskRecipients(row.id)
    },

    // 获取任务的收件人信息
    fetchTaskRecipients(taskId) {
      console.log(`正在获取任务 ${taskId} 的收件人信息`)

      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/task_recipients/${taskId}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`获取收件人失败: ${response.status}`)
          }
          return response.json()
        })
        .then(data => {
          console.log('任务收件人:', data)
          if (data.error) {
            console.warn(`获取收件人警告: ${data.error}`)
            this.$message.warning(`获取收件人可能不完整: ${data.error}`)
          }
          if (data.warning) {
            console.warn(`获取收件人警告: ${data.warning}`)
          }
          this.editForm.recipients = data.recipients || []
          // 在数据加载后应用标签样式
          this.$nextTick(() => {
            this.applyTagStyles()
          })
        })
        .catch(error => {
          console.error('获取任务收件人失败:', error)
          this.$message.warning('无法获取收件人信息，将使用空列表')
          this.editForm.recipients = [] // 使用空列表作为后备
          this.$nextTick(() => {
            this.applyTagStyles()
          })
        })
    },

    // 验证任务名规则
    validateTaskNameRule(rule, value, callback) {
      if (value && value.includes(' ')) {
        callback(new Error('任务名不支持空格输入'))
        return
      }
      callback()
    },

    // 实时验证任务名
    validateTaskName(value) {
      // 移除空格
      if (value && value.includes(' ')) {
        this.editForm.taskName = value.replace(/\s/g, '')
      }
    },

    // 检查任务名是否已存在 - 修复版本
    checkTaskNameExists(gameType, taskName) {
      // 如果是原始任务名，直接返回不存在
      if (taskName === this.originalTaskName) {
        return Promise.resolve(false)
      }

      // 检查当前表格数据中是否已存在相同游戏分类下的相同任务名
      const exists = this.tableData.some(task =>
        task.gameType === gameType &&
        task.taskName === taskName &&
        task.id !== this.editForm.id
      )

      if (exists) {
        return Promise.resolve(true)
      }

      // 如果后端API不可用，可以尝试获取完整任务列表进行检查
      return fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/tasks?gameType=${encodeURIComponent(gameType)}`)
        .then(response => {
          if (!response.ok) {
            throw new Error('获取任务列表失败')
          }
          return response.json()
        })
        .then(data => {
          const tasks = data.tasks || []
          return tasks.some(task =>
            task.taskName === taskName &&
            task.id !== this.editForm.id
          )
        })
        .catch(error => {
          console.error('检查任务名失败:', error)
          // 如果API调用失败，返回false让用户继续，但在控制台记录错误
          return false
        })
    },

    // 提交编辑表单 - 修复版本
    submitEditForm() {
      this.$refs.editForm.validate(valid => {
        if (valid) {
          this.updating = true
          const taskId = String(this.editForm.id)

          // 检查任务名是否已存在
          if (this.editForm.taskName !== this.originalTaskName) {
            this.checkTaskNameExists(this.editForm.gameType, this.editForm.taskName)
              .then(exists => {
                if (exists) {
                  this.$message.error('该游戏分类下已存在相同任务名')
                  this.updating = false
                } else {
                  this.updateTask(taskId)
                }
              })
              .catch(error => {
                console.error('检查任务名失败:', error)
                // 如果检查失败，给用户一个选择
                this.$confirm('无法验证任务名唯一性，是否继续更新?', '警告', {
                  confirmButtonText: '继续',
                  cancelButtonText: '取消',
                  type: 'warning'
                }).then(() => {
                  this.updateTask(taskId)
                }).catch(() => {
                  this.updating = false
                })
              })
          } else {
            // 任务名未变，直接更新
            this.updateTask(taskId)
          }
        } else {
          return false
        }
      })
    },

    // 更新任务
    updateTask(taskId) {
      // 验证 settings 的 JSON 格式
      if (this.editForm.settings) {
        try {
          // 只验证 JSON 格式的有效性
          JSON.parse(this.editForm.settings)
        } catch (e) {
          this.$message.error('设置参数不是有效的 JSON 格式')
          this.updating = false
          return
        }
      }

      const updateData = {
        ...this.editForm,
        is_enabled: this.editForm.isEnabled ? 1 : 0, // 转换为后端期望的格式
        settings: this.editForm.settings // 添加 settings 字段
      }

      // 如果调度状态发生了变化，需要特殊处理
      const originalEnabled = this.currentTask ? (this.currentTask.is_enabled === 1 || this.currentTask.is_enabled === true) : null
      if (originalEnabled !== null && originalEnabled !== this.editForm.isEnabled) {
        // 添加标记，告诉后端需要重新计算下次执行时间
        updateData.recalculate_next_run = true
      }

      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/task/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(data => {
              throw new Error(data.message || '更新失败')
            })
          }
          return response.json()
        })
        .then(data => {
          // 更新收件人信息
          return this.updateTaskRecipients(taskId, this.editForm.recipients)
        })
        .then(() => {
          this.$message.success('任务更新成功')
          this.updating = false
          this.editDialogVisible = false
          this.fetchTasks() // 刷新任务列表
          this.currentTask = null // 重置当前任务，确保下次编辑时重新获取收件人信息
        })
        .catch(error => {
          this.$message.error('任务更新失败: ' + error.message)
          this.updating = false
        })
    },

    // 更新任务收件人
    updateTaskRecipients(taskId, recipients) {
      return fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/task_recipients/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipients })
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(data => {
              throw new Error(data.message || '更新收件人失败')
            })
          }
          return response.json()
        })
        .catch(error => {
          console.error('更新收件人失败:', error)
          throw new Error('更新收件人失败: ' + error.message)
        })
    },

    // 取消编辑
    handleCancel() {
      if (this.updating) {
        return
      }
      this.editDialogVisible = false
    },

    // 表格选择变化
    handleSelectionChange(val) {
      this.multipleSelection = val
    },

    // 删除任务
    handleDelete(row) {
      this.deleteConfirmMessage = '此操作将永久删除该任务, 是否继续?'
      this.deleteConfirmVisible = true
      this.taskToDelete = row
      this.batchDeleteMode = false
    },

    // 处理删除确认
    handleDeleteConfirm() {
      this.deleteConfirmLoading = true

      if (this.batchDeleteMode) {
        // 批量删除逻辑
        const taskIds = this.multipleSelection.map(item => this.getTaskId(item))

        fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/tasks/batch_delete`, {
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
            this.deleteConfirmVisible = false
            this.batchDeleteMode = false
          })
          .catch(error => {
            console.error('批量删除任务失败:', error)
            this.$message.error(`批量删除任务失败: ${error.message}`)
            this.deleteConfirmVisible = false
            this.batchDeleteMode = false
          })
          .finally(() => {
            this.deleteConfirmLoading = false
          })
      } else {
        // 单个删除逻辑
        fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/task/${this.getTaskId(this.taskToDelete)}`, {
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
            this.deleteConfirmVisible = false
          })
          .catch(error => {
            console.error('删除任务失败:', error)
            this.$message.error(`删除任务失败: ${error.message}`)
            this.deleteConfirmVisible = false
          })
          .finally(() => {
            this.deleteConfirmLoading = false
          })
      }
    },

    // 批量删除任务
    handleBatchDelete() {
      if (this.multipleSelection.length === 0) {
        this.$message.warning('请至少选择一个任务')
        return
      }

      this.deleteConfirmMessage = `此操作将永久删除选中的 ${this.multipleSelection.length} 个任务, 是否继续?`
      this.deleteConfirmVisible = true
      this.batchDeleteMode = true
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
    },
    // 查看任务详情
    viewTaskDetail(row) {
      this.currentTask = row
      this.taskDetailVisible = true
      this.activeTab = 'info'

      // 加载SQL信息
      this.loadTaskSql(row.id)

      // 加载文件列表
      this.loadTaskFiles(row.id)
    },

    // 加载任务文件列表
    loadTaskFiles(taskId) {
      this.filesLoading = true
      this.taskFiles = []

      console.log(`正在加载任务 ${taskId} 的文件列表`)

      axios.get(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/task_files/${taskId}`)
        .then(response => {
          console.log('获取文件列表成功:', response.data)
          this.taskFiles = response.data
          if (this.taskFiles.length === 0) {
            this.$message.info('该任务暂无生成的报表文件')
          }
        })
        .catch(error => {
          console.error('获取文件列表失败:', error)
          this.$message.error(`获取文件列表失败: ${error.message || '未知错误'}`)
        })
        .finally(() => {
          this.filesLoading = false
        })
    },

    // 下载文件
    downloadFile(filename) {
      const taskId = this.currentTask.id
      console.log(`正在下载文件: ${filename}, 任务ID: ${taskId}`)

      // 直接使用基础URL，不添加prod-api前缀
      const baseUrl = `http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}`

      const url = `${baseUrl}/task_management/download_file/${taskId}/${encodeURIComponent(filename)}`
      console.log('下载URL:', url)

      // 在新窗口中打开下载链接
      try {
        window.open(url, '_blank')
      } catch (error) {
        console.error('下载失败:', error)
        this.$message.error(`下载失败: ${error.message || '未知错误'}`)
      }
    },

    // 格式化文件大小
    formatFileSize(size) {
      if (size < 1024) {
        return size + ' B'
      } else if (size < 1024 * 1024) {
        return (size / 1024).toFixed(2) + ' KB'
      } else if (size < 1024 * 1024 * 1024) {
        return (size / (1024 * 1024)).toFixed(2) + ' MB'
      } else {
        return (size / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
      }
    },

    // 处理下载报表按钮点击
    handleDownloadReport(row) {
      this.currentTask = row
      this.downloadDialogVisible = true
      this.loadTaskFiles(row.id)
    },

    // 格式化下次执行时间
    formatNextRunTime(row, column) {
      // 如果调度已关闭，显示为空
      if (row.is_enabled === 0 || row.is_enabled === false) {
        return '-'
      }

      // 否则使用原来的日期格式化逻辑
      const date = row[column.property]
      if (date) {
        return moment(date).utcOffset(0).format('YYYY-MM-DD HH:mm')
      } else {
        return ''
      }
    },

    // 处理标签关闭事件
    handleTagClose(tag) {
      console.log('Tag closed:', tag)
      // 在下一个DOM更新周期应用样式
      this.$nextTick(() => {
        this.applyTagStyles()
      })
    },

    // 应用标签样式
    applyTagStyles() {
      // 获取所有标签
      const tags = document.querySelectorAll('.el-select__tags .el-tag')

      // 遍历标签并应用样式
      tags.forEach(tag => {
        const value = tag.textContent || ''

        // 检查标签内容，根据内容判断类型
        if (this.emailGroups.some(group => group.group_name === value.trim())) {
          // 邮件组样式
          tag.style.backgroundColor = '#f0f9eb'
          tag.style.borderColor = '#e1f3d8'
          tag.style.color = '#67c23a'
          // 添加自定义类名
          tag.classList.add('email-group-tag')
          tag.classList.remove('email-address-tag')
        } else {
          // 个人邮件样式
          tag.style.backgroundColor = '#ecf5ff'
          tag.style.borderColor = '#d9ecff'
          tag.style.color = '#409eff'
          // 添加自定义类名
          tag.classList.add('email-address-tag')
          tag.classList.remove('email-group-tag')
        }
      })
    },
    // 获取邮件地址列表
    fetchEmails() {
      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/emails`)
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            throw new Error('获取邮件地址列表失败')
          }
        })
        .then(data => {
          console.log('邮件地址列表:', data)
          this.emails = data.items || []
          // 在数据加载后应用标签样式
          this.$nextTick(() => {
            this.applyTagStyles()
          })
        })
        .catch(error => {
          console.error('获取邮件地址失败:', error)
          this.$message.error('获取邮件地址列表失败')
        })
    },
    // 获取邮件组列表
    fetchEmailGroups() {
      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/email-groups`)
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            throw new Error('获取邮件组列表失败')
          }
        })
        .then(data => {
          console.log('邮件组列表:', data)
          this.emailGroups = data
          // 在数据加载后应用标签样式
          this.$nextTick(() => {
            this.applyTagStyles()
          })
        })
        .catch(error => {
          console.error('获取邮件组失败:', error)
          this.$message.error('获取邮件组列表失败')
        })
    },
    handleGlobalClick() {
      // 延迟执行，确保DOM已更新
      setTimeout(() => {
        this.applyTagStyles()
      }, 100)
    },
    // 添加导出功能
    exportSqlInfo() {
      // 详细输出 SQL 数据内容
      // console.log('完整的 SQL 数据:', JSON.stringify(this.sqlData, null, 2))
      // console.log('当前任务:', this.currentTask)

      // 如果有 currentTask，优先使用它
      const taskId = this.currentTask?.id || (this.sqlData.length > 0 ? this.sqlData[0].task_id : null)
      console.log('获取到的任务ID:', taskId)

      if (!taskId) {
        console.error('无法获取任务ID')
        this.$message.error('无法获取任务ID')
        return
      }

      // 从后端获取完整的任务信息
      const url = `http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/task_management/task/${taskId}`
      console.log('请求URL:', url)

      fetch(url)
        .then(response => {
          console.log('任务信息响应状态:', response.status)
          if (!response.ok) {
            return response.text().then(text => {
              console.error('任务信息响应内容:', text)
              throw new Error('获取任务信息失败')
            })
          }
          return response.json()
        })
        .then(taskData => {
          console.log('获取到的完整任务信息:', taskData)
          const currentTask = taskData

          // 按 sheet_name 对数据进行分组
          const groupedData = {}
          this.sqlData.forEach(item => {
            const sheetName = item.sheet_name || '未命名'
            if (!groupedData[sheetName]) {
              groupedData[sheetName] = []
            }

            // 创建基础数据对象
            const baseData = {
              db_name: item.db_name || '',
              format: item.format || '',
              pos: item.pos || '',
              'transpose(Y/N)': item.transpose === 1 ? 'Y' : (item.transpose === 0 ? 'N' : item.transpose)
            }

            // 检查是否有多个 SQL 字段需要合并
            const sql_parts = []
            const base_sql = item.output_sql || ''
            sql_parts.push(base_sql)

            // 检查并合并 sql1, sql2, sql3 等字段
            let i = 1
            while (`sql${i}` in item) {
              if (item[`sql${i}`]) {
                sql_parts.push(item[`sql${i}`])
              }
              i++
            }

            // 用换行连接所有 SQL 部分
            const merged_sql = sql_parts
              .map(sql => sql || '') // 处理 null 或 undefined
              .join('\n') // 用换行符连接

            // SQL 单元格字符长度上限
            const SQL_CELL_LIMIT = 32000

            // 如果合并后的 SQL 超过长度限制，需要分割
            if (merged_sql.length > SQL_CELL_LIMIT) {
              let remainingSql = merged_sql
              let sqlIndex = 0 // 从0开始，这样第一个部分会存储在 sql 字段中

              while (remainingSql.length > 0) {
                let cutIndex = SQL_CELL_LIMIT

                // 如果需要切割，寻找最近的换行
                if (remainingSql.length > SQL_CELL_LIMIT) {
                  // 在限制长度内查找最后一个换行
                  const lastNewline = remainingSql.lastIndexOf('\n', SQL_CELL_LIMIT)

                  // 如果找到换行符，在换行符后切割
                  if (lastNewline > 0) {
                    cutIndex = lastNewline + 1
                  }
                }

                const currentPart = remainingSql.slice(0, cutIndex)
                remainingSql = remainingSql.slice(cutIndex)

                // 添加 SQL 字段，从 sql 开始
                if (sqlIndex === 0) {
                  baseData.sql = currentPart
                } else {
                  baseData[`sql${sqlIndex}`] = currentPart
                }
                sqlIndex++
              }
            } else {
              baseData.sql = merged_sql
            }

            groupedData[sheetName].push(baseData)
          })

          // 创建工作簿
          const wb = XLSX.utils.book_new()

          // 按照 sheet_order 对页签进行排序
          const sheetNames = Object.keys(groupedData)
          const sortedSheetNames = sheetNames.sort((a, b) => {
            // 获取每个 sheet 的第一行数据来获取 sheet_order
            const aOrder = groupedData[a][0]?.sheet_order || 0
            const bOrder = groupedData[b][0]?.sheet_order || 0
            return aOrder - bOrder
          })

          // 为每个分组创建工作表
          sortedSheetNames.forEach(sheetName => {
            // 重命名 sql 字段为 output_sql
            const sheetData = groupedData[sheetName].map(row => {
              const newRow = { ...row }
              if ('sql' in newRow) {
                newRow.output_sql = newRow.sql
                delete newRow.sql
              }
              return newRow
            })

            const ws = XLSX.utils.json_to_sheet(sheetData)

            // 设置列宽
            const maxWidth = 50
            const colWidths = {}
            // 设置基础列的宽度
            colWidths['A'] = 15 // db_name
            colWidths['B'] = maxWidth // sql 或 sql1
            colWidths['C'] = 30 // format
            colWidths['D'] = 10 // pos
            colWidths['E'] = 15 // transpose

            // 如果有额外的 SQL 列，设置它们的宽度
            const data = groupedData[sheetName]
            if (data.length > 0) {
              const firstRow = data[0]
              const sqlColumns = Object.keys(firstRow).filter(key => key.startsWith('sql'))
              sqlColumns.forEach((_, index) => {
                // 从 F 列开始设置额外 SQL 列的宽度
                const colIndex = String.fromCharCode(70 + index) // F, G, H, ...
                colWidths[colIndex] = maxWidth
              })
            }

            ws['!cols'] = Object.keys(colWidths).map(col => ({ wch: colWidths[col] }))
            XLSX.utils.book_append_sheet(wb, ws, sheetName)
          })

          // 如果有 settings，添加 {setting} 页签
          if (currentTask && currentTask.settings) {
            console.log('处理 settings:', currentTask.settings)
            try {
              let settingsObj
              try {
                settingsObj =
                  typeof currentTask.settings === 'string'
                    ? JSON.parse(currentTask.settings)
                    : currentTask.settings
              } catch (parseError) {
                console.error('解析 settings 失败:', parseError)
                settingsObj = currentTask.settings
              }

              console.log('解析后的 settings:', settingsObj)

              // 检查是否有 freeze 配置
              if (
                settingsObj &&
                settingsObj.freeze &&
                Array.isArray(settingsObj.freeze)
              ) {
                console.log('发现 freeze 配置:', settingsObj.freeze)

                // 转换 settings 为表格数据
                const settingsData = settingsObj.freeze.map((item) => ({
                  fun: '冻结',
                  title: item.title || '',
                  config: Array.isArray(item.config)
                    ? item.config.join(';')
                    : typeof item.config === 'string'
                      ? item.config
                      : ''
                }))

                console.log('转换后的 settings 数据:', settingsData)

                if (settingsData.length > 0) {
                  // 创建 settings 工作表
                  const settingsWs = XLSX.utils.json_to_sheet(settingsData)

                  // 设置 settings 工作表的列宽
                  settingsWs['!cols'] = [
                    { wch: 10 }, // fun 列宽
                    { wch: 20 }, // title 列宽
                    { wch: 30 } // config 列宽
                  ]

                  // 添加 settings 工作表
                  XLSX.utils.book_append_sheet(wb, settingsWs, '{setting}')
                  console.log('成功添加 {setting} 工作表')
                }
              } else {
                console.log('未找到有效的 freeze 配置:', settingsObj)
              }
            } catch (e) {
              console.error('处理 settings 失败:', e)
              this.$message.warning(
                '处理配置信息时出错，{setting} 工作表可能未正确生成'
              )
            }
          } else {
            console.log('当前任务没有 settings 配置')
          }

          // 生成文件名
          const fileName = `SQL信息_${moment().format('YYYY-MM-DD_HHmmss')}.xlsx`
          // 保存文件
          XLSX.writeFile(wb, fileName)
        })
        .catch(error => {
          console.error('获取任务信息失败:', error)
          this.$message.error('获取任务信息失败，无法导出完整的 SQL 信息')
        })
    }
  }
}
</script>

<style>
/* 使用全局样式覆盖表格样式 */
.sql-info-table .el-table td,
.sql-info-table .el-table th.is-leaf {
  border-right: none;
}

.sql-info-table .el-table::before {
  height: 0;
}

.sql-info-table .el-table__fixed-right::before,
.sql-info-table .el-table__fixed::before {
  height: 0;
}

.sql-info-table .el-table--border::after,
.sql-info-table .el-table--group::after,
.sql-info-table .el-table::after {
  width: 0;
}
</style>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
  padding-top: 4px;
}

/* 调整执行时间选择器的宽度 */
.execution-time-picker {
  width: 197px; /* 调整为与执行周期选择框相同的宽度 */
}

/* 删除按钮样式 */
.delete-btn {
  color: #f56c6c;
}

/* 自定义邮件标签样式 */
::v-deep .el-tag {
  margin-right: 4px;
}

/* 邮件组样式 - 使用属性选择器 */
::v-deep .el-tag[data-path*="group-"] {
  background-color: #ecf5ff !important;
  border-color: #d9ecff !important;
  color: #409eff !important;
}

/* 邮件地址样式 - 使用属性选择器 */
::v-deep .el-tag[data-path*="email-"] {
  background-color: #f0f9eb !important;
  border-color: #e1f3d8 !important;
  color: #67c23a !important;
}
</style>
